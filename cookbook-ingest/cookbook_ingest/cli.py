from __future__ import annotations

import importlib.util
import json
import os
import shutil
import time
from pathlib import Path

import typer
from rich.console import Console
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import AppConfig, ensure_directories, load_config
from .db import JobStore
from .ingest import discover_source_files, register_job
from .logging_utils import configure_logging
from .pipeline import PipelineRunner

app = typer.Typer(help="Local cookbook ebook ingestion pipeline for Obsidian recipe notes")
console = Console()


def app_context(config_path: Path, verbose: bool) -> tuple[AppConfig, JobStore]:
    config = load_config(config_path)
    ensure_directories(config)
    store = JobStore(config.paths.db_path)
    return config, store


@app.command()
def process(
    target: Path = typer.Argument(..., exists=True, readable=True),
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Process one source file or every supported source under a directory."""
    config, store = app_context(config_path, verbose)
    files = discover_source_files(target.resolve(), config.processing.accepted_extensions)
    if not files:
        raise typer.BadParameter("No supported cookbook files found")
    for source in files:
        job = register_job(source, config, store)
        logger = configure_logging(verbose, Path(job.log_path) if job.log_path else None)
        logger.info("Registered job %s for %s", job.job_id, source)
        PipelineRunner(config, store, logger).process_job(job.job_id)
        logger.info("Completed job %s", job.job_id)


@app.command()
def retry(
    job_id: str,
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Retry a failed or partial job."""
    config, store = app_context(config_path, verbose)
    job = store.get_job(job_id)
    if job is None:
        raise typer.BadParameter(f"Unknown job: {job_id}")
    logger = configure_logging(verbose, Path(job.log_path) if job.log_path else None)
    PipelineRunner(config, store, logger).retry_job(job_id)


@app.command()
def status(
    job_id: str | None = typer.Argument(None),
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Show one job or recent jobs."""
    _, store = app_context(config_path, verbose)
    if job_id:
        job = store.get_job(job_id)
        if job is None:
            raise typer.BadParameter(f"Unknown job: {job_id}")
        console.print_json(json.dumps(job.model_dump(mode="json"), indent=2))
        return
    jobs = store.list_jobs()
    if not jobs:
        console.print("No jobs found.")
        return
    for job in jobs:
        console.print(f"{job.job_id} | {job.status.value} | staged={job.staged_count} | promoted={job.promoted_count} | {job.source_path}")


@app.command()
def review(
    job_id: str,
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """List staged recipe review records for a job."""
    config, store = app_context(config_path, verbose)
    if store.get_job(job_id) is None:
        raise typer.BadParameter(f"Unknown job: {job_id}")
    found = False
    for path in config.paths.staging_root.rglob("review.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("job_id") != job_id:
            continue
        found = True
        console.print_json(json.dumps(payload, indent=2))
    if not found:
        console.print(f"No staged recipes found for {job_id}")


@app.command()
def promote(
    staged_recipe_id: str,
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Promote one staged recipe into the live recipe tree."""
    config, store = app_context(config_path, verbose)
    logger = configure_logging(verbose)
    result = PipelineRunner(config, store, logger).promote_recipe(staged_recipe_id)
    console.print(f"Promoted {result.staged_recipe_id} -> {result.destination_dir}")


@app.command()
def doctor(
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Check local environment and integration prerequisites."""
    config, _ = app_context(config_path, verbose)
    findings: list[str] = []
    findings.append(f"python: {os.sys.version.split()[0]}")
    findings.append(f"intake_root: {config.paths.intake_root}")
    findings.append(f"vault_root_exists: {'yes' if config.paths.vault_root.exists() else 'no'}")
    findings.append(f"recipe_template_exists: {'yes' if config.paths.recipe_template.exists() else 'no'}")
    findings.append(f"ebook-convert: {'yes' if shutil.which('ebook-convert') else 'no'}")
    findings.append(f"pymupdf_installed: {'yes' if _module_exists('fitz') else 'no'}")
    findings.append(f"bs4_installed: {'yes' if _module_exists('bs4') else 'no'}")
    findings.append(f"watchdog_installed: {'yes' if _module_exists('watchdog') else 'no'}")
    findings.append(f"llm_enabled: {'yes' if config.llm.enabled else 'no'}")
    findings.append(f"llm_base_url: {config.llm.base_url}")
    findings.append(f"llm_api_key_present: {'yes' if bool(os.environ.get(config.llm.api_key_env)) else 'no'}")
    console.print("\n".join(findings))


class _WatchHandler(FileSystemEventHandler):
    def __init__(self, config: AppConfig, store: JobStore, verbose: bool):
        self.config = config
        self.store = store
        self.verbose = verbose

    def on_created(self, event) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in {ext.lower() for ext in self.config.processing.accepted_extensions}:
            return
        _wait_for_stable_copy(path, self.config.processing.copy_stability_wait_seconds)
        job = register_job(path, self.config, self.store)
        logger = configure_logging(self.verbose, Path(job.log_path) if job.log_path else None)
        PipelineRunner(self.config, self.store, logger).process_job(job.job_id)


@app.command()
def watch(
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Watch the intake folder for newly dropped cookbook files."""
    config, store = app_context(config_path, verbose)
    observer = Observer()
    handler = _WatchHandler(config, store, verbose)
    observer.schedule(handler, str(config.paths.intake_root), recursive=False)
    observer.start()
    console.print(f"Watching {config.paths.intake_root}")
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()


def _wait_for_stable_copy(path: Path, wait_seconds: float) -> None:
    previous_size = -1
    stable_passes = 0
    while stable_passes < 2:
        if not path.exists():
            return
        size = path.stat().st_size
        if size == previous_size:
            stable_passes += 1
        else:
            stable_passes = 0
        previous_size = size
        time.sleep(wait_seconds)


def _module_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


if __name__ == "__main__":
    app()

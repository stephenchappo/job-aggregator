from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .audio import require_ffmpeg
from .config import AppConfig, ensure_directories, load_config
from .db import JobStore
from .ingest import discover_mp3_files, register_job
from .logging_utils import configure_logging
from .pipeline import PipelineRunner

app = typer.Typer(help="Local meeting transcription and diarisation pipeline")
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
    dry_run: bool = typer.Option(False, "--dry-run"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Process an MP3 file or every MP3 under a directory."""
    config, store = app_context(config_path, verbose)
    files = discover_mp3_files(target.resolve())
    if not files:
        raise typer.BadParameter("No MP3 files found")

    for source in files:
        job = register_job(source, config, store)
        logger = configure_logging(verbose, Path(job.log_path) if job.log_path else None)
        logger.info("Registered job %s for %s", job.job_id, source)
        PipelineRunner(config, store, logger).process_job(job, dry_run=dry_run)
        logger.info("Completed job %s", job.job_id)


@app.command()
def retry(
    job_id: str,
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Retry a job by ID."""
    config, store = app_context(config_path, verbose)
    job = store.get_job(job_id)
    if job is None:
        raise typer.BadParameter(f"Unknown job: {job_id}")
    logger = configure_logging(verbose, Path(job.log_path) if job.log_path else None)
    PipelineRunner(config, store, logger).retry_job(job_id, dry_run=dry_run)


@app.command()
def status(
    job_id: str | None = typer.Argument(None),
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Show one job or list recent jobs."""
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
        console.print(f"{job.job_id} | {job.status.value} | {job.updated_at.isoformat()} | {job.source_path}")


@app.command()
def render(
    job_id: str,
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Re-render outputs from a JSON transcript."""
    from .models import TranscriptDocument
    from .render import write_outputs

    config, store = app_context(config_path, verbose)
    job = store.get_job(job_id)
    if job is None or not job.output_json_path:
        raise typer.BadParameter(f"No JSON output found for job: {job_id}")
    document = TranscriptDocument.model_validate_json(Path(job.output_json_path).read_text(encoding="utf-8"))
    files = write_outputs(document, config.paths.output_dir / job_id)
    store.update_job(
        job_id,
        output_markdown_path=files["markdown"],
        output_srt_path=files["srt"],
        output_vtt_path=files["vtt"],
        output_txt_path=files["txt"],
    )
    console.print(f"Rendered outputs for {job_id}")


@app.command()
def doctor(
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Check local environment and model prerequisites."""
    config, _ = app_context(config_path, verbose)
    findings: list[str] = []
    try:
        require_ffmpeg()
        findings.append("ffmpeg: ok")
    except Exception as exc:
        findings.append(f"ffmpeg: fail ({exc})")
    findings.append(f"python: {sys.version.split()[0]}")
    findings.append(f"db_path: {config.paths.db_path}")
    findings.append(f"huggingface_token_env: {config.diarization.hf_token_env}")
    findings.append(f"token_present: {'yes' if bool(os.environ.get(config.diarization.hf_token_env)) else 'no'}")
    findings.append(f"faster-whisper installed: {'yes' if _module_exists('faster_whisper') else 'no'}")
    findings.append(f"pyannote.audio installed: {'yes' if _module_exists('pyannote.audio') else 'no'}")
    findings.append(f"torch installed: {'yes' if _module_exists('torch') else 'no'}")
    findings.append(f"cuda_available: {_cuda_status()}")
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
        if path.suffix.lower() != ".mp3":
            return
        job = register_job(path, self.config, self.store)
        logger = configure_logging(self.verbose, Path(job.log_path) if job.log_path else None)
        PipelineRunner(self.config, self.store, logger).process_job(job)


@app.command()
def watch(
    config_path: Path = typer.Option(Path("config.yaml"), "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """Watch the input directory for new MP3 files."""
    config, store = app_context(config_path, verbose)
    handler = _WatchHandler(config, store, verbose)
    observer = Observer()
    observer.schedule(handler, str(config.paths.input_dir), recursive=False)
    observer.start()
    console.print(f"Watching {config.paths.input_dir}")
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()


def _module_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _cuda_status() -> str:
    if not _module_exists("torch"):
        return "unknown (torch missing)"
    try:
        import torch

        return "yes" if torch.cuda.is_available() else "no"
    except Exception as exc:
        return f"unknown ({exc})"


if __name__ == "__main__":
    app()

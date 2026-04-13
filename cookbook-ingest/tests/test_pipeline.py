import json
from pathlib import Path

from cookbook_ingest.config import AppConfig
from cookbook_ingest.db import JobStore
from cookbook_ingest.ingest import register_job
from cookbook_ingest.logging_utils import configure_logging
from cookbook_ingest.pipeline import PipelineRunner


def test_pipeline_stages_recipe_from_epub_like_source(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "sample.epub"
    source.write_text("placeholder", encoding="utf-8")

    config = AppConfig()
    config.paths.intake_root = tmp_path / "incoming"
    config.paths.jobs_dir = tmp_path / "jobs"
    config.paths.archive_dir = tmp_path / "archive"
    config.paths.failed_dir = tmp_path / "failed"
    config.paths.logs_dir = tmp_path / "logs"
    config.paths.staging_root = tmp_path / "vault/80-Recipes/00-Staging"
    config.paths.recipes_root = tmp_path / "vault/80-Recipes"
    config.paths.vault_root = tmp_path / "vault"
    config.paths.recipe_template = tmp_path / "vault/template.md"
    config.paths.db_path = tmp_path / "runtime/jobs.sqlite3"

    for path in (
        config.paths.intake_root,
        config.paths.jobs_dir,
        config.paths.archive_dir,
        config.paths.failed_dir,
        config.paths.logs_dir,
        config.paths.staging_root,
        config.paths.recipes_root,
    ):
        path.mkdir(parents=True, exist_ok=True)
    config.paths.recipe_template.write_text("template", encoding="utf-8")

    from cookbook_ingest.models import ExtractedDocument

    def fake_extract_document(*args, **kwargs):
        return ExtractedDocument(
            source_path=str(source),
            source_type="epub",
            title="Sample Book",
            text="",
            markdown="""
## Rustic Bread

Ingredients
- 500 g flour
- 350 g water
- 10 g salt

Method
1. Mix ingredients.
2. Rest 30 minutes.
3. Bake until brown.
""",
        )

    monkeypatch.setattr("cookbook_ingest.pipeline.extract_document", fake_extract_document)

    store = JobStore(config.paths.db_path)
    job = register_job(source, config, store)
    runner = PipelineRunner(config, store, configure_logging(False))
    runner.process_job(job.job_id)

    staged_reviews = list(config.paths.staging_root.rglob("review.json"))
    assert staged_reviews
    payload = json.loads(staged_reviews[0].read_text(encoding="utf-8"))
    assert payload["title"] == "Rustic Bread"

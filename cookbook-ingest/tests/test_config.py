from pathlib import Path

from cookbook_ingest.config import ensure_directories, load_config


def test_load_config_resolves_relative_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
paths:
  intake_root: data/incoming
  jobs_dir: data/jobs
  archive_dir: data/archive
  failed_dir: data/failed
  logs_dir: data/logs
  vault_root: vault
  recipe_template: vault/template.md
  recipes_root: vault/recipes
  staging_root: vault/recipes/00-Staging
  db_path: data/cookbook.sqlite3
""".strip(),
        encoding="utf-8",
    )
    config = load_config(config_path)
    assert config.paths.intake_root == (tmp_path / "data/incoming").resolve()
    assert config.paths.db_path == (tmp_path / "data/cookbook.sqlite3").resolve()


def test_ensure_directories_creates_runtime_paths(tmp_path: Path) -> None:
    config = load_config(None)
    config.paths.intake_root = tmp_path / "incoming"
    config.paths.jobs_dir = tmp_path / "jobs"
    config.paths.archive_dir = tmp_path / "archive"
    config.paths.failed_dir = tmp_path / "failed"
    config.paths.logs_dir = tmp_path / "logs"
    config.paths.staging_root = tmp_path / "vault/recipes/00-Staging"
    config.paths.db_path = tmp_path / "db/jobs.sqlite3"
    ensure_directories(config)
    assert config.paths.jobs_dir.exists()
    assert config.paths.staging_root.exists()

from pathlib import Path

from app.config import load_config


def test_load_config_resolves_relative_paths(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
paths:
  input_dir: data/input
  db_path: data/jobs.sqlite3
""",
        encoding="utf-8",
    )
    config = load_config(config_path)
    assert config.paths.input_dir == (tmp_path / "data/input").resolve()
    assert config.paths.db_path == (tmp_path / "data/jobs.sqlite3").resolve()

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PathsConfig(BaseModel):
    intake_root: Path = Path("E:/Documents/cookbook ingestion")
    jobs_dir: Path = Path("E:/Documents/cookbook ingestion/jobs")
    archive_dir: Path = Path("E:/Documents/cookbook ingestion/archive")
    failed_dir: Path = Path("E:/Documents/cookbook ingestion/failed")
    logs_dir: Path = Path("E:/Documents/cookbook ingestion/logs")
    vault_root: Path = Path("D:/Documents/Obsidian Vault")
    recipe_template: Path = Path("D:/Documents/Obsidian Vault/60-Templates/[Template] Recipe Card.md")
    recipes_root: Path = Path("D:/Documents/Obsidian Vault/80-Recipes")
    staging_root: Path = Path("D:/Documents/Obsidian Vault/80-Recipes/00-Staging")
    db_path: Path = Path("E:/Documents/cookbook ingestion/cookbook_ingest.sqlite3")


class ProcessingConfig(BaseModel):
    accepted_extensions: list[str] = Field(default_factory=lambda: [".epub", ".pdf", ".mobi"])
    copy_stability_wait_seconds: float = 2.0
    duplicate_threshold: float = 0.86
    min_recipe_score: int = 3
    ocr_text_density_threshold: int = 80


class LLMConfig(BaseModel):
    enabled: bool = False
    base_url: str = "http://localhost:11434/v1"
    api_key_env: str = "OPENAI_API_KEY"
    structuring_model: str = "Qwen/Qwen2.5-14B-Instruct"
    vision_model: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    timeout_seconds: int = 180
    max_input_chars: int = 16000


class ClassificationConfig(BaseModel):
    top_level_defaults: dict[str, list[str]] = Field(default_factory=dict)
    subcategory_keywords: dict[str, list[str]] = Field(default_factory=dict)


class AppConfig(BaseModel):
    paths: PathsConfig = Field(default_factory=PathsConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _coerce_env_value(raw: str) -> Any:
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered == "null":
        return None
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _env_overrides(prefix: str = "COOKBOOK_INGEST__") -> dict[str, Any]:
    data: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix) :].lower().split("__")
        cursor = data
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = _coerce_env_value(value)
    return data


def _resolve_path(base_dir: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def load_config(config_path: str | Path | None = None) -> AppConfig:
    root = Path(config_path or "config.yaml")
    payload: dict[str, Any] = {}
    if root.exists():
        with root.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
    payload = _deep_merge(payload, _env_overrides())
    config = AppConfig.model_validate(payload)
    base_dir = root.parent.resolve()
    config.paths = PathsConfig(
        **{
            name: _resolve_path(base_dir, getattr(config.paths, name))
            for name in PathsConfig.model_fields
        }
    )
    return config


def ensure_directories(config: AppConfig) -> None:
    for path in (
        config.paths.intake_root,
        config.paths.jobs_dir,
        config.paths.archive_dir,
        config.paths.failed_dir,
        config.paths.logs_dir,
        config.paths.staging_root,
        config.paths.db_path.parent,
    ):
        path.mkdir(parents=True, exist_ok=True)

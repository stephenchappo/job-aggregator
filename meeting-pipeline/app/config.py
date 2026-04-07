from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PathsConfig(BaseModel):
    input_dir: Path = Path("data/input")
    processing_dir: Path = Path("data/processing")
    archive_dir: Path = Path("data/archive")
    output_dir: Path = Path("data/output")
    cache_dir: Path = Path("data/cache")
    logs_dir: Path = Path("data/logs")
    db_path: Path = Path("data/meetpipe.sqlite3")


class AudioConfig(BaseModel):
    sample_rate: int = 16000
    channels: int = 1
    normalise_lufs: int = -16
    highpass_hz: int = 70


class TranscriptionConfig(BaseModel):
    engine: str = "faster-whisper"
    model: str = "large-v3"
    device: str = "cuda"
    compute_type: str = "float16"
    beam_size: int = 5
    vad_filter: bool = True
    language: str | None = None
    condition_on_previous_text: bool = True
    word_timestamps: bool = True


class DiarizationConfig(BaseModel):
    engine: str = "pyannote"
    pipeline: str = "pyannote/speaker-diarization-community-1"
    device: str = "cuda"
    min_speakers: int | None = None
    max_speakers: int | None = None
    hf_token_env: str = "HUGGINGFACE_TOKEN"


class PostprocessConfig(BaseModel):
    min_turn_seconds: float = 0.8
    merge_gap_seconds: float = 0.6
    split_on_long_pause_seconds: float = 1.2
    redact_fillers: bool = False
    paragraph_max_seconds: float = 45
    unknown_overlap_threshold: float = 0.2


class SummaryConfig(BaseModel):
    enabled: bool = False
    model: str | None = None


class AppConfig(BaseModel):
    paths: PathsConfig = Field(default_factory=PathsConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    diarization: DiarizationConfig = Field(default_factory=DiarizationConfig)
    postprocess: PostprocessConfig = Field(default_factory=PostprocessConfig)
    summary: SummaryConfig = Field(default_factory=SummaryConfig)


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


def _env_overrides(prefix: str = "MEETPIPE__") -> dict[str, Any]:
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
            name: (base_dir / getattr(config.paths, name)).resolve()
            if not getattr(config.paths, name).is_absolute()
            else getattr(config.paths, name)
            for name in PathsConfig.model_fields
        }
    )
    return config


def ensure_directories(config: AppConfig) -> None:
    for path in (
        config.paths.input_dir,
        config.paths.processing_dir,
        config.paths.archive_dir,
        config.paths.output_dir,
        config.paths.cache_dir,
        config.paths.logs_dir,
        config.paths.db_path.parent,
    ):
        path.mkdir(parents=True, exist_ok=True)

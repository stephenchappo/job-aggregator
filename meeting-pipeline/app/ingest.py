from __future__ import annotations

import hashlib
import shutil
from datetime import datetime
from pathlib import Path

from .config import AppConfig
from .db import JobStore, utc_now
from .models import JobRecord, JobStatus


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_job_id(path: Path, digest: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    stem = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in path.stem.lower()).strip("-")
    return f"{stem}-{digest[:8]}-{timestamp}"


def discover_mp3_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() == ".mp3" else []
    return sorted(item for item in path.rglob("*.mp3") if item.is_file())


def register_job(source: Path, config: AppConfig, store: JobStore) -> JobRecord:
    if source.suffix.lower() != ".mp3":
        raise ValueError(f"Unsupported input format: {source}")

    digest = sha256_file(source)
    job_id = build_job_id(source, digest)
    processing_dir = config.paths.processing_dir / job_id
    archive_dir = config.paths.archive_dir / job_id
    processing_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    processing_path = processing_dir / source.name
    archive_path = archive_dir / source.name
    shutil.copy2(source, processing_path)
    shutil.copy2(source, archive_path)

    now = utc_now()
    record = JobRecord(
        job_id=job_id,
        source_path=str(source.resolve()),
        source_sha256=digest,
        created_at=now,
        updated_at=now,
        status=JobStatus.QUEUED,
        processing_path=str(processing_path),
        archive_path=str(archive_path),
        log_path=str((config.paths.logs_dir / f"{job_id}.log").resolve()),
    )
    store.create_job(record)
    return record

from __future__ import annotations

import shutil
from pathlib import Path

from .config import AppConfig
from .db import JobStore
from .models import JobRecord
from .utils import sha256_file, slugify, timestamp_slug


def discover_source_files(target: Path, accepted_extensions: list[str]) -> list[Path]:
    accepted = {suffix.lower() for suffix in accepted_extensions}
    if target.is_file():
        return [target] if target.suffix.lower() in accepted else []
    return sorted(path for path in target.rglob("*") if path.is_file() and path.suffix.lower() in accepted)


def register_job(source: Path, config: AppConfig, store: JobStore) -> JobRecord:
    digest = sha256_file(source)
    job_id = f"{slugify(source.stem, 48)}-{digest[:8]}-{timestamp_slug()}"
    job_dir = config.paths.jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    source_copy = job_dir / "source" / source.name
    source_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, source_copy)
    log_path = config.paths.logs_dir / f"{job_id}.log"
    record = JobRecord(
        job_id=job_id,
        source_path=str(source.resolve()),
        source_sha256=digest,
        processing_dir=str(job_dir),
        log_path=str(log_path),
    )
    store.create_job(record)
    return record

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import JobRecord, JobStatus


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  source_path TEXT NOT NULL,
  source_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  status TEXT NOT NULL,
  duration_seconds REAL,
  detected_language TEXT,
  speaker_count INTEGER,
  error_message TEXT,
  processing_path TEXT,
  archive_path TEXT,
  wav_path TEXT,
  log_path TEXT,
  output_json_path TEXT,
  output_markdown_path TEXT,
  output_srt_path TEXT,
  output_vtt_path TEXT,
  output_txt_path TEXT
);
"""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def create_job(self, record: JobRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                  job_id, source_path, source_sha256, created_at, updated_at, status,
                  duration_seconds, detected_language, speaker_count, error_message,
                  processing_path, archive_path, wav_path, log_path,
                  output_json_path, output_markdown_path, output_srt_path, output_vtt_path, output_txt_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.job_id,
                    record.source_path,
                    record.source_sha256,
                    record.created_at.isoformat(),
                    record.updated_at.isoformat(),
                    record.status.value,
                    record.duration_seconds,
                    record.detected_language,
                    record.speaker_count,
                    record.error_message,
                    record.processing_path,
                    record.archive_path,
                    record.wav_path,
                    record.log_path,
                    record.output_json_path,
                    record.output_markdown_path,
                    record.output_srt_path,
                    record.output_vtt_path,
                    record.output_txt_path,
                ),
            )

    def update_job(self, job_id: str, **fields: object) -> None:
        if not fields:
            return
        fields["updated_at"] = utc_now().isoformat()
        assignments = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values()) + [job_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE jobs SET {assignments} WHERE job_id = ?", values)

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_jobs(self) -> list[JobRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        return [self._row_to_record(row) for row in rows]

    def _row_to_record(self, row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            job_id=row["job_id"],
            source_path=row["source_path"],
            source_sha256=row["source_sha256"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            status=JobStatus(row["status"]),
            duration_seconds=row["duration_seconds"],
            detected_language=row["detected_language"],
            speaker_count=row["speaker_count"],
            error_message=row["error_message"],
            processing_path=row["processing_path"],
            archive_path=row["archive_path"],
            wav_path=row["wav_path"],
            log_path=row["log_path"],
            output_json_path=row["output_json_path"],
            output_markdown_path=row["output_markdown_path"],
            output_srt_path=row["output_srt_path"],
            output_vtt_path=row["output_vtt_path"],
            output_txt_path=row["output_txt_path"],
        )

from __future__ import annotations

import logging
import traceback
from pathlib import Path

from .align import assign_speakers_to_segments, build_turns
from .audio import preprocess_audio
from .config import AppConfig
from .db import JobStore
from .diarize import diarize_audio
from .models import AudioMetadata, JobRecord, JobStatus, ModelMetadata, TranscriptDocument
from .postprocess import clean_turns
from .render import write_outputs
from .summary import maybe_summarise
from .transcribe import transcribe_audio


class PipelineRunner:
    def __init__(self, config: AppConfig, store: JobStore, logger: logging.Logger):
        self.config = config
        self.store = store
        self.logger = logger

    def process_job(self, job: JobRecord, dry_run: bool = False) -> TranscriptDocument | None:
        job_dir = self.config.paths.processing_dir / job.job_id
        output_dir = self.config.paths.output_dir / job.job_id
        input_path = Path(job.processing_path or job.source_path)

        if dry_run:
            self.logger.info("Dry run for %s: %s", job.job_id, input_path)
            return None

        try:
            self.store.update_job(job.job_id, status=JobStatus.PREPROCESSING.value)
            self.logger.info("Preprocessing audio")
            wav_path, audio_probe = preprocess_audio(input_path, job_dir, self.config)
            self.store.update_job(
                job.job_id,
                wav_path=str(wav_path.resolve()),
                duration_seconds=audio_probe.get("duration_seconds"),
            )

            self.store.update_job(job.job_id, status=JobStatus.DIARIZING.value)
            self.logger.info("Running diarisation")
            diarization_segments = diarize_audio(wav_path, self.config)

            self.store.update_job(job.job_id, status=JobStatus.TRANSCRIBING.value)
            self.logger.info("Running transcription")
            language, transcript_segments = transcribe_audio(wav_path, self.config)
            self.store.update_job(job.job_id, detected_language=language)

            self.store.update_job(job.job_id, status=JobStatus.ALIGNING.value)
            self.logger.info("Aligning speakers")
            assigned_segments = assign_speakers_to_segments(
                transcript_segments,
                diarization_segments,
                self.config.postprocess,
            )
            raw_turns = build_turns(assigned_segments, self.config.postprocess.merge_gap_seconds)

            self.store.update_job(job.job_id, status=JobStatus.POSTPROCESSING.value)
            self.logger.info("Cleaning turns")
            clean = clean_turns(raw_turns, self.config.postprocess)

            document = TranscriptDocument(
                job_id=job.job_id,
                created_at=job.created_at,
                detected_language=language,
                speaker_count=len({segment.speaker for segment in diarization_segments}),
                status=JobStatus.RENDERING,
                audio=AudioMetadata(
                    source_path=job.source_path,
                    source_sha256=job.source_sha256,
                    original_filename=input_path.name,
                    duration_seconds=audio_probe.get("duration_seconds"),
                    sample_rate=audio_probe.get("sample_rate"),
                    channels=audio_probe.get("channels"),
                    preprocessed_wav_path=str(wav_path.resolve()),
                ),
                models=ModelMetadata(
                    transcription_engine=self.config.transcription.engine,
                    transcription_model=self.config.transcription.model,
                    transcription_device=self.config.transcription.device,
                    diarization_engine=self.config.diarization.engine,
                    diarization_pipeline=self.config.diarization.pipeline,
                    diarization_device=self.config.diarization.device,
                ),
                diarization_segments=diarization_segments,
                transcript_segments=assigned_segments,
                speaker_turns_raw=raw_turns,
                speaker_turns_clean=clean,
            )

            self.store.update_job(job.job_id, status=JobStatus.RENDERING.value, speaker_count=document.speaker_count)
            self.logger.info("Rendering outputs")
            files = write_outputs(document, output_dir)
            self.store.update_job(
                job.job_id,
                output_json_path=files["json"],
                output_markdown_path=files["markdown"],
                output_srt_path=files["srt"],
                output_vtt_path=files["vtt"],
                output_txt_path=files["txt"],
            )

            if self.config.summary.enabled:
                self.store.update_job(job.job_id, status=JobStatus.SUMMARISING.value)
                document.summary = maybe_summarise(document, self.config)

            document.status = JobStatus.DONE
            self.store.update_job(job.job_id, status=JobStatus.DONE.value)
            return document
        except Exception as exc:
            self.store.update_job(job.job_id, status=JobStatus.FAILED.value, error_message=str(exc))
            self.logger.error("Job %s failed: %s", job.job_id, exc)
            self.logger.debug("%s", traceback.format_exc())
            raise

    def retry_job(self, job_id: str, dry_run: bool = False) -> TranscriptDocument | None:
        job = self.store.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        self.store.update_job(job.job_id, error_message=None)
        return self.process_job(job, dry_run=dry_run)

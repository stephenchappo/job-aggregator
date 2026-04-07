from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    PREPROCESSING = "preprocessing"
    DIARIZING = "diarizing"
    TRANSCRIBING = "transcribing"
    ALIGNING = "aligning"
    POSTPROCESSING = "postprocessing"
    RENDERING = "rendering"
    SUMMARISING = "summarising"
    DONE = "done"
    FAILED = "failed"


class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float
    probability: float | None = None
    speaker: str | None = None


class TranscriptSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    avg_logprob: float | None = None
    no_speech_prob: float | None = None
    compression_ratio: float | None = None
    speaker: str | None = None
    words: list[WordTimestamp] = Field(default_factory=list)


class SpeakerSegment(BaseModel):
    speaker: str
    start: float
    end: float
    duration: float | None = None
    confidence: float | None = None


class SpeakerTurn(BaseModel):
    speaker: str
    start: float
    end: float
    text: str
    confidence: float | None = None
    words: list[WordTimestamp] = Field(default_factory=list)
    source_segment_ids: list[int] = Field(default_factory=list)


class AudioMetadata(BaseModel):
    source_path: str
    source_sha256: str
    original_filename: str
    duration_seconds: float | None = None
    sample_rate: int | None = None
    channels: int | None = None
    preprocessed_wav_path: str | None = None


class ModelMetadata(BaseModel):
    transcription_engine: str
    transcription_model: str
    transcription_device: str
    diarization_engine: str
    diarization_pipeline: str
    diarization_device: str


class SummaryData(BaseModel):
    summary: str | None = None
    decisions: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    raw: dict[str, Any] | None = None


class RenderMetadata(BaseModel):
    rendered_at: datetime
    files: dict[str, str] = Field(default_factory=dict)


class TranscriptDocument(BaseModel):
    job_id: str
    created_at: datetime
    detected_language: str | None = None
    speaker_count: int = 0
    status: JobStatus
    audio: AudioMetadata
    models: ModelMetadata
    diarization_segments: list[SpeakerSegment] = Field(default_factory=list)
    transcript_segments: list[TranscriptSegment] = Field(default_factory=list)
    speaker_turns_raw: list[SpeakerTurn] = Field(default_factory=list)
    speaker_turns_clean: list[SpeakerTurn] = Field(default_factory=list)
    render_metadata: RenderMetadata | None = None
    summary: SummaryData | None = None
    warnings: list[str] = Field(default_factory=list)


class JobRecord(BaseModel):
    job_id: str
    source_path: str
    source_sha256: str
    created_at: datetime
    updated_at: datetime
    status: JobStatus
    duration_seconds: float | None = None
    detected_language: str | None = None
    speaker_count: int | None = None
    error_message: str | None = None
    processing_path: str | None = None
    archive_path: str | None = None
    wav_path: str | None = None
    log_path: str | None = None
    output_json_path: str | None = None
    output_markdown_path: str | None = None
    output_srt_path: str | None = None
    output_vtt_path: str | None = None
    output_txt_path: str | None = None

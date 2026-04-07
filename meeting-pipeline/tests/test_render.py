from datetime import datetime, timezone

from app.models import AudioMetadata, JobStatus, ModelMetadata, SpeakerTurn, TranscriptDocument
from app.render import format_timestamp, render_markdown, render_srt, render_vtt


def _document() -> TranscriptDocument:
    return TranscriptDocument(
        job_id="job-1",
        created_at=datetime.now(timezone.utc),
        detected_language="en",
        speaker_count=2,
        status=JobStatus.DONE,
        audio=AudioMetadata(
            source_path="/tmp/source.mp3",
            source_sha256="abc",
            original_filename="source.mp3",
            duration_seconds=90,
        ),
        models=ModelMetadata(
            transcription_engine="faster-whisper",
            transcription_model="large-v3",
            transcription_device="cuda",
            diarization_engine="pyannote",
            diarization_pipeline="community-1",
            diarization_device="cuda",
        ),
        speaker_turns_clean=[
            SpeakerTurn(speaker="SPEAKER_00", start=1.0, end=3.0, text="Hello there"),
        ],
    )


def test_format_timestamp():
    assert format_timestamp(1.234) == "00:00:01:234"
    assert format_timestamp(1.234, ",") == "00:00:01,234"


def test_render_markdown_contains_speaker_lines():
    text = render_markdown(_document())
    assert "SPEAKER_00: Hello there" in text
    assert "# Meeting transcript" in text


def test_render_subtitles():
    doc = _document()
    assert "SPEAKER_00: Hello there" in render_srt(doc.speaker_turns_clean)
    assert render_vtt(doc.speaker_turns_clean).startswith("WEBVTT")

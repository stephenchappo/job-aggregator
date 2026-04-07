from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import RenderMetadata, SpeakerTurn, TranscriptDocument


def format_timestamp(seconds: float, separator: str = ":") -> str:
    millis = round(seconds * 1000)
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}{separator}{ms:03}"


def format_clock(seconds: float) -> str:
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"


def render_markdown(document: TranscriptDocument) -> str:
    lines = [
        "# Meeting transcript",
        f"Source: {document.audio.original_filename}",
        f"Language: {document.detected_language or 'unknown'}",
        f"Speakers detected: {document.speaker_count}",
        f"Duration: {format_clock(document.audio.duration_seconds or 0)}",
        "",
        "## Transcript",
    ]
    for turn in document.speaker_turns_clean or document.speaker_turns_raw:
        lines.append(f"[{format_clock(turn.start)}] {turn.speaker}: {turn.text}")
    lines.extend(
        [
            "",
            "## Metadata",
            f"- Job ID: {document.job_id}",
            f"- Model: {document.models.transcription_engine} {document.models.transcription_model}",
            f"- Diarisation: {document.models.diarization_engine} {document.models.diarization_pipeline}",
        ]
    )
    return "\n".join(lines) + "\n"


def render_text(turns: list[SpeakerTurn]) -> str:
    return "\n".join(f"{turn.speaker}: {turn.text}" for turn in turns) + "\n"


def _subtitle_blocks(turns: list[SpeakerTurn], webvtt: bool = False) -> str:
    lines: list[str] = ["WEBVTT", ""] if webvtt else []
    for index, turn in enumerate(turns, start=1):
        if not webvtt:
            lines.append(str(index))
        start = format_timestamp(turn.start, "." if webvtt else ",")
        end = format_timestamp(turn.end, "." if webvtt else ",")
        lines.append(f"{start} --> {end}")
        lines.append(f"{turn.speaker}: {turn.text}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_srt(turns: list[SpeakerTurn]) -> str:
    return _subtitle_blocks(turns, webvtt=False)


def render_vtt(turns: list[SpeakerTurn]) -> str:
    return _subtitle_blocks(turns, webvtt=True)


def write_outputs(document: TranscriptDocument, output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "transcript.json"
    md_path = output_dir / "transcript.md"
    txt_path = output_dir / "transcript.txt"
    srt_path = output_dir / "transcript.srt"
    vtt_path = output_dir / "transcript.vtt"

    json_path.write_text(json.dumps(document.model_dump(mode="json"), indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(document), encoding="utf-8")
    txt_path.write_text(render_text(document.speaker_turns_clean or document.speaker_turns_raw), encoding="utf-8")
    srt_path.write_text(render_srt(document.speaker_turns_clean or document.speaker_turns_raw), encoding="utf-8")
    vtt_path.write_text(render_vtt(document.speaker_turns_clean or document.speaker_turns_raw), encoding="utf-8")

    document.render_metadata = RenderMetadata(
        rendered_at=datetime.now(timezone.utc),
        files={
            "json": str(json_path.resolve()),
            "markdown": str(md_path.resolve()),
            "txt": str(txt_path.resolve()),
            "srt": str(srt_path.resolve()),
            "vtt": str(vtt_path.resolve()),
        },
    )
    json_path.write_text(json.dumps(document.model_dump(mode="json"), indent=2), encoding="utf-8")
    return document.render_metadata.files

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .config import AppConfig


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is not installed or not on PATH")
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe is not installed or not on PATH")


def preprocess_audio(input_path: Path, job_dir: Path, config: AppConfig) -> tuple[Path, dict]:
    require_ffmpeg()
    output_path = job_dir / "preprocessed.wav"
    loudnorm = f"loudnorm=I={config.audio.normalise_lufs}:LRA=11:TP=-1.5"
    highpass = f"highpass=f={config.audio.highpass_hz}"
    filters = f"{loudnorm},{highpass}"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        str(config.audio.channels),
        "-ar",
        str(config.audio.sample_rate),
        "-af",
        filters,
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg preprocessing failed: {result.stderr.strip()}")
    metadata = probe_audio(output_path)
    return output_path, metadata


def probe_audio(audio_path: Path) -> dict:
    command = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(audio_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")
    payload = json.loads(result.stdout)
    stream = next((item for item in payload.get("streams", []) if item.get("codec_type") == "audio"), {})
    fmt = payload.get("format", {})
    return {
        "duration_seconds": float(fmt["duration"]) if fmt.get("duration") else None,
        "sample_rate": int(stream["sample_rate"]) if stream.get("sample_rate") else None,
        "channels": int(stream["channels"]) if stream.get("channels") else None,
    }

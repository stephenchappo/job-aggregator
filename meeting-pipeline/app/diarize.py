from __future__ import annotations

import inspect
import wave
from pathlib import Path

import numpy as np

from .config import AppConfig
from .models import SpeakerSegment


def diarize_audio(audio_path: Path, config: AppConfig) -> list[SpeakerSegment]:
    try:
        import torch
        from pyannote.audio import Pipeline
    except ImportError as exc:
        raise RuntimeError("pyannote.audio is not installed. Install the 'ml' extras.") from exc

    token = None
    if config.diarization.hf_token_env:
        import os

        token = os.environ.get(config.diarization.hf_token_env)
    if not token:
        raise RuntimeError(
            f"Missing Hugging Face token in environment variable {config.diarization.hf_token_env}"
        )

    from_pretrained = Pipeline.from_pretrained
    kwargs = {}
    signature = inspect.signature(from_pretrained)
    if "token" in signature.parameters:
        kwargs["token"] = token
    else:
        kwargs["use_auth_token"] = token

    pipeline = from_pretrained(config.diarization.pipeline, **kwargs)
    if config.diarization.device.startswith("cuda"):
        pipeline.to(torch.device(config.diarization.device))

    waveform, sample_rate = load_waveform(audio_path, torch)
    diarization_input = {
        "waveform": waveform,
        "sample_rate": sample_rate,
    }

    diarization = pipeline(
        diarization_input,
        min_speakers=config.diarization.min_speakers,
        max_speakers=config.diarization.max_speakers,
    )

    exclusive = getattr(diarization, "exclusive_speaker_diarization", None)
    timeline = exclusive if exclusive is not None else diarization
    segments: list[SpeakerSegment] = []
    for segment, _, speaker in timeline.itertracks(yield_label=True):
        start = float(segment.start)
        end = float(segment.end)
        segments.append(
            SpeakerSegment(
                speaker=str(speaker),
                start=start,
                end=end,
                duration=max(0.0, end - start),
            )
    )
    return segments


def load_waveform(audio_path: Path, torch_module) -> tuple[object, int]:
    with wave.open(str(audio_path), "rb") as handle:
        sample_rate = handle.getframerate()
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        frames = handle.getnframes()
        raw = handle.readframes(frames)

    if sample_width == 2:
        dtype = np.int16
        scale = 32768.0
    elif sample_width == 4:
        dtype = np.int32
        scale = 2147483648.0
    else:
        raise RuntimeError(f"Unsupported WAV sample width: {sample_width} bytes")

    array = np.frombuffer(raw, dtype=dtype).astype(np.float32) / scale
    if channels > 1:
        array = array.reshape(-1, channels).T
    else:
        array = array.reshape(1, -1)

    waveform = torch_module.from_numpy(array)
    return waveform, sample_rate

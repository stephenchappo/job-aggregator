from __future__ import annotations

from pathlib import Path
import warnings

from .config import AppConfig
from .models import TranscriptSegment, WordTimestamp


def transcribe_audio(audio_path: Path, config: AppConfig) -> tuple[str | None, list[TranscriptSegment]]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("faster-whisper is not installed. Install the 'ml' extras.") from exc

    try:
        segments, info = _run_transcription(
            WhisperModel,
            audio_path,
            model_name=config.transcription.model,
            device=config.transcription.device,
            compute_type=config.transcription.compute_type,
            beam_size=config.transcription.beam_size,
            vad_filter=config.transcription.vad_filter,
            language=config.transcription.language,
            condition_on_previous_text=config.transcription.condition_on_previous_text,
            word_timestamps=config.transcription.word_timestamps,
        )
    except RuntimeError as exc:
        message = str(exc)
        if not _should_fallback_to_cpu(message):
            raise
        warnings.warn(
            "Configured GPU transcription failed; retrying faster-whisper on CPU with int8.",
            RuntimeWarning,
        )
        segments, info = _run_transcription(
            WhisperModel,
            audio_path,
            model_name=config.transcription.model,
            device="cpu",
            compute_type="int8",
            beam_size=config.transcription.beam_size,
            vad_filter=config.transcription.vad_filter,
            language=config.transcription.language,
            condition_on_previous_text=config.transcription.condition_on_previous_text,
            word_timestamps=config.transcription.word_timestamps,
        )

    collected: list[TranscriptSegment] = []
    for index, segment in enumerate(segments):
        words = [
            WordTimestamp(
                word=item.word.strip(),
                start=float(item.start),
                end=float(item.end),
                probability=getattr(item, "probability", None),
            )
            for item in (segment.words or [])
            if item.start is not None and item.end is not None
        ]
        collected.append(
            TranscriptSegment(
                id=index,
                start=float(segment.start),
                end=float(segment.end),
                text=segment.text.strip(),
                avg_logprob=getattr(segment, "avg_logprob", None),
                no_speech_prob=getattr(segment, "no_speech_prob", None),
                compression_ratio=getattr(segment, "compression_ratio", None),
                words=words,
            )
        )
    language = getattr(info, "language", None)
    return language, collected


def _run_transcription(
    whisper_model_cls,
    audio_path: Path,
    *,
    model_name: str,
    device: str,
    compute_type: str,
    beam_size: int,
    vad_filter: bool,
    language: str | None,
    condition_on_previous_text: bool,
    word_timestamps: bool,
):
    model = whisper_model_cls(
        model_name,
        device=device,
        compute_type=compute_type,
    )
    return model.transcribe(
        str(audio_path),
        beam_size=beam_size,
        vad_filter=vad_filter,
        language=language,
        condition_on_previous_text=condition_on_previous_text,
        word_timestamps=word_timestamps,
    )


def _should_fallback_to_cpu(message: str) -> bool:
    lowered = message.lower()
    return "libcublas" in lowered or "cuda" in lowered or "cudnn" in lowered

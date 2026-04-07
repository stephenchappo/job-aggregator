from __future__ import annotations

from collections import defaultdict

from .config import PostprocessConfig
from .models import SpeakerSegment, SpeakerTurn, TranscriptSegment, WordTimestamp


def compute_overlap(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    return max(0.0, min(end_a, end_b) - max(start_a, start_b))


def assign_speaker(start: float, end: float, diarization: list[SpeakerSegment], threshold: float) -> tuple[str, float]:
    overlaps: dict[str, float] = defaultdict(float)
    window = max(end - start, 0.001)
    for segment in diarization:
        overlap = compute_overlap(start, end, segment.start, segment.end)
        if overlap > 0:
            overlaps[segment.speaker] += overlap
    if not overlaps:
        return "UNKNOWN", 0.0
    speaker, overlap = max(overlaps.items(), key=lambda item: item[1])
    ratio = overlap / window
    if ratio < threshold:
        return "UNKNOWN", ratio
    return speaker, ratio


def dominant_word_speaker(words: list[WordTimestamp]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for word in words:
        counts[word.speaker or "UNKNOWN"] += 1
    return max(counts.items(), key=lambda item: item[1])[0] if counts else "UNKNOWN"


def assign_speakers_to_segments(
    transcript_segments: list[TranscriptSegment],
    diarization_segments: list[SpeakerSegment],
    config: PostprocessConfig,
) -> list[TranscriptSegment]:
    assigned: list[TranscriptSegment] = []
    for segment in transcript_segments:
        if segment.words:
            for word in segment.words:
                speaker, _ = assign_speaker(
                    word.start,
                    word.end,
                    diarization_segments,
                    config.unknown_overlap_threshold,
                )
                word.speaker = speaker
            speaker = dominant_word_speaker(segment.words)
            assigned.append(segment.model_copy(update={"speaker": speaker, "words": segment.words}))
            continue
        speaker, _ = assign_speaker(
            segment.start,
            segment.end,
            diarization_segments,
            config.unknown_overlap_threshold,
        )
        assigned.append(segment.model_copy(update={"speaker": speaker}))
    return assigned


def build_turns(
    transcript_segments: list[TranscriptSegment],
    merge_gap_seconds: float,
) -> list[SpeakerTurn]:
    turns: list[SpeakerTurn] = []
    for segment in transcript_segments:
        if not segment.text.strip():
            continue
        speaker = segment.speaker or "UNKNOWN"
        if turns:
            previous = turns[-1]
            gap = segment.start - previous.end
            if previous.speaker == speaker and gap <= merge_gap_seconds:
                previous.end = segment.end
                previous.text = f"{previous.text} {segment.text}".strip()
                previous.words.extend(segment.words)
                previous.source_segment_ids.append(segment.id)
                continue
        turns.append(
            SpeakerTurn(
                speaker=speaker,
                start=segment.start,
                end=segment.end,
                text=segment.text.strip(),
                words=list(segment.words),
                source_segment_ids=[segment.id],
            )
        )
    return turns

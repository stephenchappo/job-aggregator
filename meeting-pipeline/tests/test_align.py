from app.align import assign_speaker, build_turns, compute_overlap
from app.models import SpeakerSegment, TranscriptSegment


def test_compute_overlap():
    assert compute_overlap(0.0, 2.0, 1.0, 3.0) == 1.0
    assert compute_overlap(0.0, 1.0, 1.0, 2.0) == 0.0


def test_assign_speaker_unknown_under_threshold():
    diarization = [SpeakerSegment(speaker="SPEAKER_00", start=0.0, end=0.1)]
    speaker, confidence = assign_speaker(0.0, 1.0, diarization, threshold=0.5)
    assert speaker == "UNKNOWN"
    assert confidence < 0.5


def test_build_turns_merges_adjacent_speaker_segments():
    segments = [
        TranscriptSegment(id=0, start=0.0, end=1.0, text="Hello", speaker="SPEAKER_00"),
        TranscriptSegment(id=1, start=1.2, end=2.0, text="world", speaker="SPEAKER_00"),
    ]
    turns = build_turns(segments, merge_gap_seconds=0.5)
    assert len(turns) == 1
    assert turns[0].text == "Hello world"

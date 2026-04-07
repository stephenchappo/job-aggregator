from __future__ import annotations

import re

from .config import PostprocessConfig
from .models import SpeakerTurn


FILLER_RE = re.compile(r"\b(um+|uh+|erm|ah)\b", re.IGNORECASE)


def clean_turns(turns: list[SpeakerTurn], config: PostprocessConfig) -> list[SpeakerTurn]:
    cleaned: list[SpeakerTurn] = []
    for turn in turns:
        text = turn.text.strip()
        if config.redact_fillers:
            text = FILLER_RE.sub("", text)
            text = re.sub(r"\s{2,}", " ", text).strip()
        if cleaned:
            prev = cleaned[-1]
            gap = turn.start - prev.end
            if prev.speaker == turn.speaker and gap <= config.merge_gap_seconds:
                prev.end = turn.end
                prev.text = f"{prev.text} {text}".strip()
                prev.words.extend(turn.words)
                prev.source_segment_ids.extend(turn.source_segment_ids)
                continue
        cleaned.append(turn.model_copy(update={"text": text}))
    return cleaned

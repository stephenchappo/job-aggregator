from __future__ import annotations

from .config import AppConfig
from .models import SummaryData, TranscriptDocument


def maybe_summarise(document: TranscriptDocument, config: AppConfig) -> SummaryData | None:
    if not config.summary.enabled:
        return None
    raise NotImplementedError("Summary generation is reserved for a later phase.")

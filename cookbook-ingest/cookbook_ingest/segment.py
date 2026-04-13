from __future__ import annotations

import re

from .config import AppConfig
from .models import ExtractedDocument, RecipeSegment
from .utils import slugify


INGREDIENT_PATTERNS = [
    r"\bingredients?\b",
    r"\bcups?\b",
    r"\btablespoons?\b",
    r"\bteaspoons?\b",
    r"\bgrams?\b",
    r"\boz\b",
    r"\bpounds?\b",
]

METHOD_PATTERNS = [
    r"\bmethod\b",
    r"\bdirections?\b",
    r"\binstructions?\b",
    r"^\s*1[.)]",
    r"\bmix\b",
    r"\bbake\b",
    r"\bboil\b",
]


def segment_recipes(document: ExtractedDocument, config: AppConfig) -> list[RecipeSegment]:
    lines = [line.strip() for line in document.markdown.splitlines()]
    segments: list[RecipeSegment] = []
    current_title = ""
    current_lines: list[str] = []
    page_hits: list[int] = []

    def flush() -> None:
        nonlocal current_title, current_lines, page_hits
        body = "\n".join(current_lines).strip()
        score = _segment_score(current_title, body)
        if current_title and body and score >= config.processing.min_recipe_score:
            segments.append(
                RecipeSegment(
                    segment_id=slugify(current_title),
                    title=current_title,
                    text=body,
                    score=score,
                    source_pages=sorted(set(page_hits)),
                )
            )
        current_title = ""
        current_lines = []
        page_hits = []

    for raw_line in lines:
        page_match = re.match(r"## Page (\d+)$", raw_line)
        if page_match:
            page_hits.append(int(page_match.group(1)))
            continue
        if raw_line.startswith("# "):
            flush()
            current_title = raw_line[2:].strip()
            continue
        if raw_line.startswith("## "):
            heading = raw_line[3:].strip()
            if current_title and current_lines and len(current_lines) > 4:
                flush()
            current_title = heading
            continue
        if current_title:
            current_lines.append(raw_line)

    flush()
    return segments


def _segment_score(title: str, body: str) -> int:
    score = 0
    if len(title.split()) >= 2:
        score += 1
    lowered = f"{title}\n{body}".lower()
    if any(re.search(pattern, lowered, flags=re.MULTILINE) for pattern in INGREDIENT_PATTERNS):
        score += 2
    if any(re.search(pattern, lowered, flags=re.MULTILINE) for pattern in METHOD_PATTERNS):
        score += 2
    if lowered.count("\n- ") >= 3 or len(re.findall(r"^\s*[-*]\s+", body, flags=re.MULTILINE)) >= 3:
        score += 1
    return score

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path

from .config import AppConfig
from .models import RecipeCandidate


def classify_candidate(candidate: RecipeCandidate, config: AppConfig) -> tuple[str, str, bool]:
    text = f"{candidate.title}\n{candidate.category}\n{candidate.course}\n" + "\n".join(candidate.tags)
    lowered = text.lower()

    top_level = "Baking"
    for group, keywords in config.classification.top_level_defaults.items():
        if any(keyword in lowered for keyword in keywords):
            top_level = "Baking" if group == "baking" else "Savory"
            break

    subcategory = ""
    for name, keywords in config.classification.subcategory_keywords.items():
        if any(keyword in lowered for keyword in keywords):
            subcategory = name
            break

    confident = bool(subcategory or candidate.category)
    return top_level, subcategory or "Needs Classification", confident


def find_duplicate_matches(candidate: RecipeCandidate, recipes_root: Path, threshold: float) -> list[str]:
    if not recipes_root.exists():
        return []
    matches: list[str] = []
    target = _normalise(candidate.title)
    for path in recipes_root.rglob("*.md"):
        if "00-Staging" in str(path):
            continue
        score = SequenceMatcher(a=target, b=_normalise(path.stem)).ratio()
        if score >= threshold:
            matches.append(str(path))
    return sorted(matches)[:5]


def suggested_live_dir(candidate: RecipeCandidate, top_level: str, subcategory: str, recipes_root: Path) -> Path:
    book = candidate.source_book or "Unknown Source"
    folder_name = f"{candidate.title} - {book}"
    return recipes_root / top_level / subcategory / folder_name


def _normalise(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum())

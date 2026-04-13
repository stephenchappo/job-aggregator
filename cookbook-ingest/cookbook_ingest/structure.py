from __future__ import annotations

import re

from .models import ExtractedDocument, RecipeCandidate, RecipeSegment, RecipeTiming
from .utils import title_case


SECTION_HEADINGS = {
    "ingredients": ("ingredients",),
    "method": ("method", "directions", "instructions", "preparation"),
    "notes": ("notes", "source notes", "headnote"),
    "timing": ("timing", "time"),
}


def build_candidate(segment: RecipeSegment, document: ExtractedDocument, source_book: str) -> RecipeCandidate:
    parsed = _split_sections(segment.text)
    ingredients = _parse_ingredients(parsed["ingredients"] or segment.text)
    method = _parse_method(parsed["method"] or segment.text)
    notes = _parse_notes(parsed["notes"])
    timing = _parse_timing(parsed["timing"] or segment.text)
    title = title_case(segment.title.strip())
    best_for = notes[0] if notes else ""
    source_pages = _page_span(segment.source_pages)
    tags = _infer_tags(title, ingredients, method)
    course = _infer_course(title, tags)
    category = _infer_category(title, tags)
    confidence = min(0.35 + (0.1 * segment.score) + (0.08 * bool(ingredients)) + (0.08 * bool(method)), 0.95)
    return RecipeCandidate(
        title=title,
        tags=tags,
        course=course,
        category=category,
        yield_amount=_extract_simple_value(segment.text, r"\b(?:yield|makes|serves)\b[: ]+([^\n]+)"),
        active_time=_extract_simple_value(segment.text, r"\bactive time\b[: ]+([^\n]+)"),
        total_time=_extract_simple_value(segment.text, r"\btotal time\b[: ]+([^\n]+)"),
        difficulty=_infer_difficulty(segment.text),
        source=source_book + (f", pp. {source_pages}" if source_pages else ""),
        source_book=source_book,
        source_pages=source_pages,
        best_for=best_for,
        ingredients=ingredients,
        method=method,
        timing=timing,
        proposed_schedule=[],
        source_notes=notes,
        audhd_tags=tags,
        confidence=confidence,
        source_excerpt=segment.text[:2000],
    )


def _split_sections(text: str) -> dict[str, str]:
    buckets = {"ingredients": "", "method": "", "notes": "", "timing": ""}
    current = None
    lines = text.splitlines()
    for line in lines:
        stripped = line.strip().rstrip(":")
        lowered = stripped.lower()
        matched = None
        for bucket, names in SECTION_HEADINGS.items():
            if lowered in names:
                matched = bucket
                break
        if matched:
            current = matched
            continue
        if current:
            buckets[current] += line + "\n"
    return buckets


def _parse_ingredients(text: str) -> list[str]:
    ingredients: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("-", "*")):
            ingredients.append(stripped[1:].strip())
            continue
        if re.match(r"^\d", stripped) and any(unit in stripped.lower() for unit in ("cup", "tbsp", "tsp", "gram", "ounce", "oz", "lb")):
            ingredients.append(stripped)
    return ingredients


def _parse_method(text: str) -> list[str]:
    method: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^\d+[.)]\s+", stripped):
            method.append(re.sub(r"^\d+[.)]\s+", "", stripped))
        elif stripped.startswith(("-", "*")) and any(verb in stripped.lower() for verb in ("mix", "bake", "cook", "stir", "knead", "proof", "rest", "drain")):
            method.append(stripped[1:].strip())
    return method


def _parse_notes(text: str) -> list[str]:
    return [line.strip("- ").strip() for line in text.splitlines() if line.strip()]


def _parse_timing(text: str) -> RecipeTiming:
    return RecipeTiming(
        prep=_extract_simple_value(text, r"\bprep\b[: ]+([^\n]+)"),
        cook_bake=_extract_simple_value(text, r"\b(?:cook|bake)\b[: ]+([^\n]+)"),
        rest_proof_chill=_extract_simple_value(text, r"\b(?:rest|proof|chill)\b[: ]+([^\n]+)"),
        total=_extract_simple_value(text, r"\btotal\b[: ]+([^\n]+)"),
    )


def _extract_simple_value(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _page_span(pages: list[int]) -> str:
    if not pages:
        return ""
    if len(pages) == 1:
        return str(pages[0])
    return f"{min(pages)}-{max(pages)}"


def _infer_tags(title: str, ingredients: list[str], method: list[str]) -> list[str]:
    text = f"{title}\n" + "\n".join(ingredients + method)
    tags = ["recipe"]
    keywords = {
        "baking": ("bread", "cookie", "cake", "dough", "bake"),
        "bread": ("bread", "loaf", "sourdough"),
        "pizza": ("pizza", "tomato sauce", "fillets"),
        "sauce": ("sauce", "tomato"),
        "sweet": ("cookie", "cake", "sweet", "dessert", "brownie"),
        "savory": ("sauce", "pizza", "roast", "soup"),
    }
    lowered = text.lower()
    for tag, terms in keywords.items():
        if any(term in lowered for term in terms):
            tags.append(tag)
    return sorted(set(tags))


def _infer_course(title: str, tags: list[str]) -> str:
    lowered = title.lower()
    if "bread" in lowered:
        return "bread"
    if "sauce" in lowered:
        return "sauce"
    if "cookie" in lowered or "cake" in lowered:
        return "dessert"
    if "pizza" in lowered:
        return "pizza"
    if "bread" in tags:
        return "bread"
    return ""


def _infer_category(title: str, tags: list[str]) -> str:
    lowered = title.lower()
    if "bread" in lowered:
        return "Baking/Bread"
    if "dough" in lowered:
        return "Baking/Pizza Dough"
    if "cookie" in lowered or "cake" in lowered:
        return "Baking/Sweets"
    if "pizza" in lowered or "sauce" in lowered:
        return "Savory/Pizza"
    if "savory" in tags:
        return "Savory"
    return "Baking" if "baking" in tags else ""


def _infer_difficulty(text: str) -> str:
    lowered = text.lower()
    if "beginner" in lowered or "easy" in lowered:
        return "easy" if "easy" in lowered else "beginner"
    if "advanced" in lowered:
        return "advanced"
    return ""

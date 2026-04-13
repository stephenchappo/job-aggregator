from __future__ import annotations

from pathlib import Path

from .models import RecipeCandidate, ReviewRecord
from .utils import write_json


FRONTMATTER_ORDER = [
    "date",
    "tags",
    "course",
    "category",
    "yield",
    "active_time",
    "total_time",
    "start_time",
    "difficulty",
    "equipment",
    "source",
    "source_book",
    "source_pages",
    "recipe_folder",
    "original_scan_note",
    "original_scan_files",
    "recipe_card_front_image",
    "recipe_card_back_image",
    "recipe_card_status",
]


def render_staged_recipe(candidate: RecipeCandidate, stage_dir: Path, today: str) -> dict[str, Path]:
    stage_dir.mkdir(parents=True, exist_ok=True)
    note_path = stage_dir / f"{candidate.title}.md"
    excerpt_path = stage_dir / "source-excerpt.md"
    candidate_json = stage_dir / "candidate.json"
    note_path.write_text(render_markdown(candidate, today), encoding="utf-8")
    excerpt_path.write_text(candidate.source_excerpt.strip() + "\n", encoding="utf-8")
    write_json(candidate_json, candidate.model_dump(mode="json", by_alias=True))
    return {
        "note": note_path,
        "excerpt": excerpt_path,
        "candidate_json": candidate_json,
    }


def write_review_record(review: ReviewRecord, stage_dir: Path) -> Path:
    path = stage_dir / "review.json"
    write_json(path, review.model_dump(mode="json"))
    return path


def render_markdown(candidate: RecipeCandidate, today: str) -> str:
    frontmatter = {
        "date": today,
        "tags": candidate.tags or ["recipe"],
        "course": candidate.course,
        "category": candidate.category,
        "yield": candidate.yield_amount,
        "active_time": candidate.active_time,
        "total_time": candidate.total_time,
        "start_time": candidate.start_time,
        "difficulty": candidate.difficulty,
        "equipment": candidate.equipment,
        "source": candidate.source,
        "source_book": candidate.source_book,
        "source_pages": candidate.source_pages,
        "recipe_folder": candidate.recipe_folder,
        "original_scan_note": candidate.original_scan_note,
        "original_scan_files": candidate.original_scan_files,
        "recipe_card_front_image": candidate.recipe_card_front_image,
        "recipe_card_back_image": candidate.recipe_card_back_image,
        "recipe_card_status": candidate.recipe_card_status,
    }
    lines = ["---"]
    for key in FRONTMATTER_ORDER:
        value = frontmatter[key]
        lines.extend(_yaml_field(key, value))
    lines.append("---")
    lines.append(f"# {candidate.title}")
    lines.append("")
    lines.append("> [!recipe-card]")
    lines.append(f"> **Yield:** {candidate.yield_amount}")
    lines.append(f"> **Active Time:** {candidate.active_time}")
    lines.append(f"> **Total Time:** {candidate.total_time}")
    lines.append(f"> **Start Time:** {candidate.start_time or 'Fill in when planning'}")
    lines.append(f"> **Best For:** {candidate.best_for}")
    tags_line = " ".join(f"#{tag}" for tag in candidate.tags)
    lines.append(f"> **Tags:** {tags_line}".rstrip())
    lines.append(">")
    lines.append("> ## Ingredients")
    for item in candidate.ingredients or [""]:
        lines.append(f"> - {item}")
    lines.append(">")
    lines.append("> ## Method")
    for index, step in enumerate(candidate.method or [""], start=1):
        lines.append(f"> {index}. {step}")
    lines.append(">")
    lines.append("> Front card layout goal: use columns so ingredients and method share the front whenever they fit cleanly.")
    lines.append(">")
    lines.append("> ## Proposed Schedule")
    for item in candidate.proposed_schedule or [""]:
        lines.append(f"> - {item}")
    lines.append(">")
    lines.append("> ## Notes")
    for item in candidate.source_notes or [""]:
        lines.append(f"> - {item}")
    lines.append("")
    lines.append("## Recipe Card Front")
    if candidate.recipe_card_status == "pending-render":
        lines.append("- Pending recipe card front render.")
    else:
        lines.append(f"![[{candidate.recipe_card_front_image}]]")
    lines.append("")
    lines.append("## Recipe Card Back")
    if candidate.recipe_card_status == "pending-render":
        lines.append("- Pending recipe card back render.")
    else:
        lines.append(f"![[{candidate.recipe_card_back_image}]]")
    lines.append("")
    lines.append("## Full Recipe")
    lines.append("")
    lines.append("### Ingredients")
    for item in candidate.ingredients or [""]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### Method")
    for index, step in enumerate(candidate.method or [""], start=1):
        lines.append(f"{index}. {step}")
    lines.append("")
    lines.append("### Timing")
    lines.append(f"- Prep: {candidate.timing.prep}")
    lines.append(f"- Cook/Bake: {candidate.timing.cook_bake}")
    lines.append(f"- Rest/Proof/Chill: {candidate.timing.rest_proof_chill}")
    lines.append(f"- Total: {candidate.timing.total or candidate.total_time}")
    lines.append("")
    lines.append("### Proposed Schedule")
    if candidate.proposed_schedule:
        lines.append(f"- Start: {candidate.start_time or 'choose a start time in the frontmatter when planning'}")
        for item in candidate.proposed_schedule:
            lines.append(f"- {item}")
    else:
        lines.append("- Start:")
        lines.append("- ")
    lines.append("")
    lines.append("### Source Notes")
    for item in candidate.source_notes or ["- "]:
        lines.append(f"- {item}" if item else "- ")
    lines.append("")
    lines.append("## Original Scan Images")
    lines.append(f"See [[{candidate.original_scan_note}]].")
    lines.append("")
    lines.append("### Scan File References")
    if candidate.original_scan_files:
        for item in candidate.original_scan_files:
            lines.append(f"- `{item}`")
    else:
        lines.append("- Add the raw image filenames from `80-Recipes/zz Scans`")
    lines.append("")
    lines.append("### AuDHD Tags")
    lines.append(" ".join(f"#{tag}" for tag in candidate.audhd_tags or ["recipe"]).strip())
    return "\n".join(lines).rstrip() + "\n"


def _yaml_field(key: str, value: object) -> list[str]:
    if isinstance(value, list):
        lines = [f"{key}:"]
        if value:
            lines.extend([f"  - {item}" for item in value])
        return lines
    if value == "" or value is None:
        return [f"{key}:"]
    if isinstance(value, str) and ("[" in value or "]" in value or ":" in value or "/" in value or "\\" in value or "\"" in value):
        return [f'{key}: "{value}"']
    return [f"{key}: {value}"]

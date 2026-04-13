from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    staged = "staged"
    failed = "failed"
    archived = "archived"


class RecipeTiming(BaseModel):
    prep: str = ""
    cook_bake: str = ""
    rest_proof_chill: str = ""
    total: str = ""


class RecipeCandidate(BaseModel):
    title: str = ""
    tags: list[str] = Field(default_factory=list)
    course: str = ""
    category: str = ""
    yield_amount: str = Field(default="", alias="yield")
    active_time: str = ""
    total_time: str = ""
    start_time: str = ""
    difficulty: str = ""
    equipment: list[str] = Field(default_factory=list)
    source: str = ""
    source_book: str = ""
    source_pages: str = ""
    recipe_folder: str = ""
    original_scan_note: str = ""
    original_scan_files: list[str] = Field(default_factory=list)
    recipe_card_front_image: str = ""
    recipe_card_back_image: str = ""
    recipe_card_status: str = "pending-render"
    best_for: str = ""
    ingredients: list[str] = Field(default_factory=list)
    method: list[str] = Field(default_factory=list)
    timing: RecipeTiming = Field(default_factory=RecipeTiming)
    proposed_schedule: list[str] = Field(default_factory=list)
    source_notes: list[str] = Field(default_factory=list)
    audhd_tags: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    duplicate_matches: list[str] = Field(default_factory=list)
    staged_recipe_id: str = ""
    source_excerpt: str = ""

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def normalise_lists(self) -> "RecipeCandidate":
        self.tags = [value.strip().lower() for value in self.tags if value and value.strip()]
        self.ingredients = [value.strip() for value in self.ingredients if value and value.strip()]
        self.method = [value.strip() for value in self.method if value and value.strip()]
        self.equipment = [value.strip() for value in self.equipment if value and value.strip()]
        self.proposed_schedule = [value.strip() for value in self.proposed_schedule if value and value.strip()]
        self.source_notes = [value.strip() for value in self.source_notes if value and value.strip()]
        self.audhd_tags = [value.strip().lower() for value in self.audhd_tags if value and value.strip()]
        return self

    @property
    def is_valid(self) -> bool:
        return bool(self.title and self.ingredients and self.method and self.source_book)


class RecipeSegment(BaseModel):
    segment_id: str
    title: str
    text: str
    score: int
    source_pages: list[int] = Field(default_factory=list)


class ExtractedDocument(BaseModel):
    source_path: str
    source_type: str
    title: str = ""
    author: str = ""
    text: str
    markdown: str
    metadata: dict[str, str] = Field(default_factory=dict)
    page_map: dict[str, str] = Field(default_factory=dict)
    used_ocr: bool = False


class JobRecord(BaseModel):
    job_id: str
    source_path: str
    source_sha256: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    status: JobStatus = JobStatus.pending
    error_message: str | None = None
    processing_dir: str | None = None
    archive_path: str | None = None
    failed_path: str | None = None
    log_path: str | None = None
    document_json_path: str | None = None
    document_markdown_path: str | None = None
    staged_count: int = 0
    promoted_count: int = 0


class ReviewRecord(BaseModel):
    staged_recipe_id: str
    job_id: str
    title: str
    source_book: str
    source_pages: str = ""
    stage_path: str
    suggested_live_path: str
    confidence: float
    warnings: list[str] = Field(default_factory=list)
    duplicate_matches: list[str] = Field(default_factory=list)
    ready_for_promotion: bool = False
    promoted_at: str | None = None
    promoted_path: str | None = None


class PromotionResult(BaseModel):
    staged_recipe_id: str
    source_dir: Path
    destination_dir: Path

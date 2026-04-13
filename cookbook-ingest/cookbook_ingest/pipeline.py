from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from .classify import classify_candidate, find_duplicate_matches, suggested_live_dir
from .config import AppConfig
from .db import JobStore
from .extractors import ExtractionError, extract_document
from .llm_client import LLMClient
from .models import PromotionResult, RecipeCandidate, ReviewRecord
from .render import render_staged_recipe, write_review_record
from .segment import segment_recipes
from .structure import build_candidate
from .utils import slugify, write_json


class PipelineRunner:
    def __init__(self, config: AppConfig, store: JobStore, logger):
        self.config = config
        self.store = store
        self.logger = logger
        self.llm_client = LLMClient(config.llm)

    def process_job(self, job_id: str) -> None:
        job = self.store.get_job(job_id)
        if job is None:
            raise ValueError(f"Unknown job: {job_id}")
        job_dir = Path(job.processing_dir or "")
        source_copy_dir = job_dir / "source"
        source_files = [path for path in source_copy_dir.iterdir() if path.is_file()]
        if not source_files:
            raise FileNotFoundError("No copied source file found for job")
        source_copy = source_files[0]
        self.store.update_job(job_id, status="processing")
        try:
            document = extract_document(source_copy, job_dir, self.config, self.llm_client)
            document_json = job_dir / "document.json"
            document_markdown = job_dir / "document.md"
            write_json(document_json, document.model_dump(mode="json"))
            document_markdown.write_text(document.markdown, encoding="utf-8")
            self.store.update_job(
                job_id,
                document_json_path=str(document_json),
                document_markdown_path=str(document_markdown),
            )

            segments = segment_recipes(document, self.config)
            staged_count = 0
            for index, segment in enumerate(segments, start=1):
                candidate = self._candidate_from_segment(segment, document)
                if not candidate.is_valid:
                    continue
                staged_count += 1
                self._stage_candidate(job_id, candidate, index)

            archive_path = self._archive_source(Path(job.source_path))
            self.store.update_job(
                job_id,
                status="staged",
                staged_count=staged_count,
                archive_path=str(archive_path),
            )
        except Exception as exc:
            failed_path = self._move_to_failed(Path(job.source_path))
            self.store.update_job(
                job_id,
                status="failed",
                error_message=str(exc),
                failed_path=str(failed_path) if failed_path else None,
            )
            if isinstance(exc, ExtractionError):
                self.logger.error("Extraction failed for %s: %s", job_id, exc)
            else:
                self.logger.exception("Job %s failed", job_id)
            raise

    def retry_job(self, job_id: str) -> None:
        self.process_job(job_id)

    def promote_recipe(self, staged_recipe_id: str) -> PromotionResult:
        for review_path in self.config.paths.staging_root.rglob("review.json"):
            review = ReviewRecord.model_validate_json(review_path.read_text(encoding="utf-8"))
            if review.staged_recipe_id != staged_recipe_id:
                continue
            source_dir = Path(review.stage_path)
            destination_dir = Path(review.suggested_live_path)
            destination_dir.parent.mkdir(parents=True, exist_ok=True)
            if destination_dir.exists():
                raise FileExistsError(f"Live recipe already exists: {destination_dir}")
            shutil.move(str(source_dir), str(destination_dir))
            review.promoted_at = datetime.utcnow().isoformat()
            review.promoted_path = str(destination_dir)
            write_review_record(review, destination_dir)
            job = self.store.get_job(review.job_id)
            promoted_count = 1 if job is None else job.promoted_count + 1
            self.store.update_job(review.job_id, promoted_count=promoted_count)
            return PromotionResult(
                staged_recipe_id=staged_recipe_id,
                source_dir=source_dir,
                destination_dir=destination_dir,
            )
        raise FileNotFoundError(f"No staged recipe found for {staged_recipe_id}")

    def _candidate_from_segment(self, segment, document) -> RecipeCandidate:
        llm_candidate = self.llm_client.structure_recipe(segment.text)
        candidate = llm_candidate or build_candidate(segment, document, source_book=document.title or Path(document.source_path).stem)
        if not candidate.source_book:
            candidate.source_book = document.title or Path(document.source_path).stem
        if not candidate.source:
            candidate.source = candidate.source_book + (f", pp. {candidate.source_pages}" if candidate.source_pages else "")
        if not candidate.original_scan_note:
            candidate.original_scan_note = f"{candidate.title} - Source Scans"
        if not candidate.recipe_card_front_image:
            candidate.recipe_card_front_image = f"{candidate.title} - Recipe Card.png"
        if not candidate.recipe_card_back_image:
            candidate.recipe_card_back_image = f"{candidate.title} - Recipe Card Back.png"
        return candidate

    def _stage_candidate(self, job_id: str, candidate: RecipeCandidate, index: int) -> None:
        top_level, subcategory, confident = classify_candidate(candidate, self.config)
        candidate.duplicate_matches = find_duplicate_matches(
            candidate, self.config.paths.recipes_root, self.config.processing.duplicate_threshold
        )
        if candidate.duplicate_matches:
            candidate.warnings.append("Possible duplicate recipe already exists in the vault.")
        if not confident:
            candidate.warnings.append("Category mapping needs review.")
        candidate.recipe_folder = str(suggested_live_dir(candidate, top_level, subcategory, Path("80-Recipes")).as_posix())
        staged_recipe_id = f"{job_id}-{index:03d}-{slugify(candidate.title, 40)}"
        candidate.staged_recipe_id = staged_recipe_id

        if confident:
            stage_dir = self.config.paths.staging_root / candidate.source_book / f"{candidate.title} - {candidate.source_book}"
        else:
            stage_dir = self.config.paths.staging_root / "Needs Classification" / f"{candidate.title} - {candidate.source_book}"
        files = render_staged_recipe(candidate, stage_dir, today=datetime.now().strftime("%Y-%m-%d"))
        live_dir = suggested_live_dir(candidate, top_level, subcategory, self.config.paths.recipes_root)
        review = ReviewRecord(
            staged_recipe_id=staged_recipe_id,
            job_id=job_id,
            title=candidate.title,
            source_book=candidate.source_book,
            source_pages=candidate.source_pages,
            stage_path=str(stage_dir),
            suggested_live_path=str(live_dir),
            confidence=candidate.confidence,
            warnings=candidate.warnings,
            duplicate_matches=candidate.duplicate_matches,
            ready_for_promotion=bool(candidate.is_valid and not candidate.duplicate_matches and confident),
        )
        write_review_record(review, stage_dir)
        self.logger.info("Staged recipe %s at %s", staged_recipe_id, files["note"])

    def _archive_source(self, source_path: Path) -> Path:
        if not source_path.exists():
            return self.config.paths.archive_dir / source_path.name
        destination = self.config.paths.archive_dir / source_path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(destination))
        return destination

    def _move_to_failed(self, source_path: Path) -> Path | None:
        if not source_path.exists():
            return None
        destination = self.config.paths.failed_dir / source_path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(destination))
        return destination

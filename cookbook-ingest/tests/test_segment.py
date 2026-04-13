from cookbook_ingest.config import AppConfig
from cookbook_ingest.models import ExtractedDocument
from cookbook_ingest.segment import segment_recipes


def test_segment_recipes_detects_recipe_like_sections() -> None:
    document = ExtractedDocument(
        source_path="sample.epub",
        source_type="epub",
        title="Sample Book",
        text="",
        markdown="""
# Intro

Welcome to the book.

## Rustic Bread

Ingredients
- 500 g flour
- 350 g water
- 10 g salt

Method
1. Mix ingredients.
2. Rest 30 minutes.
3. Bake until brown.
""",
    )
    segments = segment_recipes(document, AppConfig())
    assert len(segments) == 1
    assert segments[0].title == "Rustic Bread"

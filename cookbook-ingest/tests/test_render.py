from cookbook_ingest.models import RecipeCandidate
from cookbook_ingest.render import render_markdown


def test_render_markdown_matches_recipe_shape() -> None:
    candidate = RecipeCandidate(
        title="Basic Bread",
        tags=["recipe", "baking", "bread"],
        course="bread",
        category="Baking/Bread",
        yield_amount="2 loaves",
        active_time="20 minutes",
        total_time="3 hours",
        source="Example Book, pp. 1-2",
        source_book="Example Book",
        source_pages="1-2",
        recipe_folder="80-Recipes/Baking/Bread/Basic Bread - Example Book",
        original_scan_note="Basic Bread - Source Scans",
        recipe_card_front_image="Basic Bread - Recipe Card.png",
        recipe_card_back_image="Basic Bread - Recipe Card Back.png",
        best_for="Sandwich bread",
        ingredients=["500 g flour", "350 g water"],
        method=["Mix.", "Bake."],
        audhd_tags=["recipe", "baking", "bread"],
    )
    markdown = render_markdown(candidate, today="2026-04-07")
    assert markdown.startswith("---\ndate: 2026-04-07")
    assert "# Basic Bread" in markdown
    assert "> [!recipe-card]" in markdown
    assert "## Full Recipe" in markdown
    assert "### AuDHD Tags" in markdown

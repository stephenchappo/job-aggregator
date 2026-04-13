from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from urllib import error, request

from .config import LLMConfig
from .models import RecipeCandidate


STRUCTURE_PROMPT = """You are extracting a cookbook recipe into strict JSON.
Return only valid JSON matching this schema:
{
  "title": "",
  "tags": [],
  "course": "",
  "category": "",
  "yield": "",
  "active_time": "",
  "total_time": "",
  "start_time": "",
  "difficulty": "",
  "equipment": [],
  "source": "",
  "source_book": "",
  "source_pages": "",
  "recipe_folder": "",
  "original_scan_note": "",
  "original_scan_files": [],
  "recipe_card_front_image": "",
  "recipe_card_back_image": "",
  "recipe_card_status": "pending-render",
  "best_for": "",
  "ingredients": [],
  "method": [],
  "timing": { "prep": "", "cook_bake": "", "rest_proof_chill": "", "total": "" },
  "proposed_schedule": [],
  "source_notes": [],
  "audhd_tags": []
}
Rules:
- no markdown fences
- leave unknown fields empty
- do not invent source pages
- keep ingredients and method as arrays of strings
- tags and audhd_tags should be short lowercase terms
"""

OCR_PROMPT = """Transcribe this cookbook page into concise markdown that preserves recipe titles, ingredient bullets, numbered steps, and time notes. Return only markdown."""


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.enabled = config.enabled
        self.vision_enabled = config.enabled and bool(config.vision_model)

    def structure_recipe(self, segment_text: str) -> RecipeCandidate | None:
        if not self.enabled:
            return None
        payload = {
            "model": self.config.structuring_model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": STRUCTURE_PROMPT},
                {"role": "user", "content": segment_text[: self.config.max_input_chars]},
            ],
        }
        result = self._post_json(payload)
        if result is None:
            return None
        content = _extract_message_content(result)
        if not content:
            return None
        try:
            return RecipeCandidate.model_validate_json(content)
        except Exception:
            return None

    def ocr_image_to_markdown(self, image_path: Path) -> str:
        if not self.vision_enabled:
            return ""
        image_data = base64.b64encode(image_path.read_bytes()).decode("ascii")
        payload = {
            "model": self.config.vision_model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": OCR_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": OCR_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
                    ],
                },
            ],
        }
        result = self._post_json(payload)
        if result is None:
            return ""
        return _extract_message_content(result)

    def _post_json(self, payload: dict) -> dict | None:
        endpoint = self.config.base_url.rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        api_key = os.environ.get(self.config.api_key_env)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        req = request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError):
            return None


def _extract_message_content(result: dict) -> str:
    choices = result.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, list):
        texts = []
        for item in content:
            if item.get("type") == "text" and item.get("text"):
                texts.append(item["text"])
        return "\n".join(texts).strip()
    return str(content).strip()

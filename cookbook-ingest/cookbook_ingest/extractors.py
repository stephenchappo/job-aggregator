from __future__ import annotations

import re
import subprocess
import zipfile
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

from .config import AppConfig
from .llm_client import LLMClient
from .models import ExtractedDocument
from .utils import normalise_whitespace


class ExtractionError(RuntimeError):
    pass


def extract_document(source: Path, work_dir: Path, config: AppConfig, llm_client: LLMClient | None = None) -> ExtractedDocument:
    suffix = source.suffix.lower()
    if suffix == ".epub":
        return extract_epub(source)
    if suffix == ".mobi":
        return extract_mobi(source, work_dir)
    if suffix == ".pdf":
        return extract_pdf(source, work_dir, config, llm_client)
    raise ExtractionError(f"Unsupported source type: {source.suffix}")


def extract_epub(source: Path) -> ExtractedDocument:
    with zipfile.ZipFile(source) as archive:
        container = archive.read("META-INF/container.xml")
        root = ET.fromstring(container)
        opf_path = root.find(".//{*}rootfile").attrib["full-path"]
        opf_dir = Path(opf_path).parent
        opf = ET.fromstring(archive.read(opf_path))
        metadata = {
            _strip_namespace(element.tag): (element.text or "").strip()
            for element in opf.findall(".//{*}metadata/*")
            if (element.text or "").strip()
        }
        manifest = {
            item.attrib["id"]: item.attrib["href"]
            for item in opf.findall(".//{*}manifest/{*}item")
            if item.attrib.get("href")
        }
        spine = [item.attrib["idref"] for item in opf.findall(".//{*}spine/{*}itemref")]
        markdown_parts: list[str] = []
        text_parts: list[str] = []
        for item_id in spine:
            href = manifest.get(item_id)
            if not href:
                continue
            chapter_path = str((opf_dir / href).as_posix())
            soup = BeautifulSoup(archive.read(chapter_path), "html.parser")
            for tag in soup(["script", "style", "nav"]):
                tag.decompose()
            chapter_markdown = _html_to_markdown(soup)
            if chapter_markdown.strip():
                markdown_parts.append(chapter_markdown.strip())
                text_parts.append(soup.get_text("\n", strip=True))
    return ExtractedDocument(
        source_path=str(source),
        source_type="epub",
        title=metadata.get("title", source.stem),
        author=metadata.get("creator", ""),
        text=normalise_whitespace("\n\n".join(text_parts)),
        markdown=normalise_whitespace("\n\n".join(markdown_parts)),
        metadata=metadata,
    )


def extract_mobi(source: Path, work_dir: Path) -> ExtractedDocument:
    target = work_dir / f"{source.stem}.epub"
    cmd = ["ebook-convert", str(source), str(target)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise ExtractionError("ebook-convert not found; calibre is required for MOBI support") from exc
    except subprocess.CalledProcessError as exc:
        raise ExtractionError(exc.stderr.strip() or "MOBI conversion failed") from exc
    return extract_epub(target)


def extract_pdf(source: Path, work_dir: Path, config: AppConfig, llm_client: LLMClient | None = None) -> ExtractedDocument:
    try:
        import fitz
    except ImportError as exc:
        raise ExtractionError("PyMuPDF is required for PDF extraction") from exc

    pdf = fitz.open(source)
    text_parts: list[str] = []
    markdown_parts: list[str] = []
    page_map: dict[str, str] = {}
    total_text = 0
    for index, page in enumerate(pdf, start=1):
        page_text = page.get_text("text").strip()
        if page_text:
            page_map[str(index)] = page_text[:500]
        total_text += len(page_text)
        if page_text:
            markdown_parts.append(f"## Page {index}\n\n{page_text}")
            text_parts.append(page_text)

    used_ocr = False
    avg_chars = total_text / max(len(pdf), 1)
    if avg_chars < config.processing.ocr_text_density_threshold and llm_client is not None and llm_client.vision_enabled:
        used_ocr = True
        text_parts = []
        markdown_parts = []
        for index, page in enumerate(pdf, start=1):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            image_path = work_dir / f"page-{index:04d}.png"
            pix.save(image_path)
            ocr_markdown = llm_client.ocr_image_to_markdown(image_path)
            if ocr_markdown.strip():
                markdown_parts.append(f"## Page {index}\n\n{ocr_markdown}")
                page_text = re.sub(r"[#>*`]", "", ocr_markdown)
                text_parts.append(page_text)
                page_map[str(index)] = page_text[:500]

    pdf.close()
    text = normalise_whitespace("\n\n".join(text_parts))
    if not text.strip():
        raise ExtractionError("No extractable text found in PDF")
    return ExtractedDocument(
        source_path=str(source),
        source_type="pdf",
        title=source.stem,
        text=text,
        markdown=normalise_whitespace("\n\n".join(markdown_parts)),
        page_map=page_map,
        used_ocr=used_ocr,
    )


def _html_to_markdown(soup: BeautifulSoup) -> str:
    lines: list[str] = []
    for element in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = unescape(element.get_text(" ", strip=True))
        if not text:
            continue
        if element.name == "h1":
            lines.append(f"# {text}")
        elif element.name == "h2":
            lines.append(f"## {text}")
        elif element.name == "h3":
            lines.append(f"### {text}")
        elif element.name == "li":
            lines.append(f"- {text}")
        else:
            lines.append(text)
    return "\n\n".join(lines)


def _strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]

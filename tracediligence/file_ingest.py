from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


MAX_CHARS_PER_FILE = 30_000
MAX_TOTAL_CHARS = 60_000


def _read_pdf(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _read_docx(data: bytes) -> str:
    document = Document(BytesIO(data))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def _read_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def extract_uploaded_files(uploaded_files: list) -> tuple[str, list[dict]]:
    """Extract supported Streamlit uploads and return prompt text plus source metadata."""
    sections: list[str] = []
    sources: list[dict] = []
    total_chars = 0

    for uploaded in uploaded_files or []:
        filename = getattr(uploaded, "name", "uploaded_document")
        suffix = Path(filename).suffix.lower()
        data = uploaded.getvalue()

        if suffix == ".pdf":
            text = _read_pdf(data)
        elif suffix == ".docx":
            text = _read_docx(data)
        elif suffix in {".txt", ".md", ".csv"}:
            text = _read_text(data)
        else:
            continue

        remaining = MAX_TOTAL_CHARS - total_chars
        if remaining <= 0:
            break
        excerpt = text[: min(MAX_CHARS_PER_FILE, remaining)].strip()
        total_chars += len(excerpt)

        if excerpt:
            sections.append(f"\n--- UPLOADED DOCUMENT: {filename} ---\n{excerpt}")
            sources.append(
                {
                    "title": filename,
                    "url": f"uploaded://{filename}",
                    "source_type": "uploaded_document",
                    "publication_date": None,
                    "reliability_score": 0.80,
                }
            )

    return "\n".join(sections), sources

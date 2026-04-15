from __future__ import annotations

import hashlib
from pathlib import Path
from pypdf import PdfReader

def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)

def checksum_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_uploaded_text(file_path: str, content_type: str) -> str:
    suffix = Path(file_path).suffix.lower()

    if content_type == "application/pdf" or suffix == ".pdf":
        return extract_pdf_text(file_path)

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_pdf_text(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks

def naive_token_count(text: str) -> int:
    return max(1, len(text.split()))

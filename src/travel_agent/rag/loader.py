"""Markdown knowledge document loader.

Loads .md files from the knowledge directory, splits them into
header-delimited chunks with metadata (source, section, destination).
"""

import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """A single chunk of knowledge with metadata."""

    text: str = Field(..., description="Chunk text content")
    source: str = Field(..., description="Source filename")
    destination: str = Field(default="", description="City / destination name")
    section: str = Field(default="", description="Header section title")
    chunk_id: int = Field(default=0, description="Chunk sequence number")


# ── Default knowledge directory ──
_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def load_knowledge_dir(directory: Optional[str | Path] = None) -> list[Chunk]:
    """Load all .md files from the knowledge directory and chunk them.

    Args:
        directory: Path to the directory containing .md files.
            If None, uses the default knowledge/ directory.

    Returns:
        List of Chunk objects with text, source, destination metadata.
    """
    if directory is None:
        directory = _KNOWLEDGE_DIR
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return []

    chunks: list[Chunk] = []
    md_files = sorted(dir_path.glob("*.md"))

    for filepath in md_files:
        destination = _extract_destination(filepath.stem)
        file_chunks = _chunk_markdown(filepath, destination)
        chunks.extend(file_chunks)

    return chunks


def _extract_destination(stem: str) -> str:
    """Extract destination city name from filename stem."""
    # Files like "beijing.md" → "北京"
    name_map = {
        "beijing": "北京",
        "shanghai": "上海",
        "chengdu": "成都",
        "hangzhou": "杭州",
        "guangzhou": "广州",
        "shenzhen": "深圳",
        "xian": "西安",
        "chongqing": "重庆",
    }
    return name_map.get(stem.lower(), stem)


def _chunk_markdown(filepath: Path, destination: str) -> list[Chunk]:
    """Split a markdown file into header-delimited chunks.

    Each H2 (## Section) or H3 (### Subsection) becomes a separate chunk,
    prefixed by the document title (H1) for context.
    """
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")

    chunks: list[Chunk] = []
    title = ""
    current_section = ""
    current_lines: list[str] = []
    chunk_id = 0

    for line in lines:
        # H1 — document title
        if line.startswith("# ") and not line.startswith("## "):
            if current_lines and current_section:
                chunks.append(_make_chunk(current_lines, filepath.name, destination, current_section, chunk_id))
                chunk_id += 1
                current_lines = []
            title = re.sub(r"^#\s+", "", line).strip()
            current_section = title
            current_lines = [f"# {title}"]
            continue

        # H2 / H3 — section boundary
        if line.startswith("##") and current_lines:
            chunks.append(_make_chunk(current_lines, filepath.name, destination, current_section, chunk_id))
            chunk_id += 1
            current_lines = [f"# {title}"]

        current_section = re.sub(r"^#{1,3}\s+", "", line).strip() if line.startswith("##") else current_section
        current_lines.append(line)

    # Last chunk
    if current_lines:
        chunks.append(_make_chunk(current_lines, filepath.name, destination, current_section, chunk_id))

    return chunks


def _make_chunk(lines: list[str], source: str, destination: str, section: str, chunk_id: int) -> Chunk:
    """Build a Chunk from accumulated lines."""
    text = "\n".join(lines).strip()
    return Chunk(
        text=text,
        source=source,
        destination=destination,
        section=section,
        chunk_id=chunk_id,
    )

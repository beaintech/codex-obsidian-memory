from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FRONTMATTER_BOUNDARY = "---"


@dataclass(frozen=True)
class MarkdownChunk:
    """A heading-scoped piece of a Markdown note."""

    path: str
    title: str
    heading: str
    content: str
    ordinal: int


def _strip_frontmatter(lines: list[str]) -> list[str]:
    if not lines or lines[0].strip() != FRONTMATTER_BOUNDARY:
        return lines
    for index in range(1, min(len(lines), 200)):
        if lines[index].strip() == FRONTMATTER_BOUNDARY:
            return lines[index + 1 :]
    return lines


def chunk_markdown(path: Path, vault: Path) -> list[MarkdownChunk]:
    """Split a Markdown file at headings while retaining source metadata."""

    text = path.read_text(encoding="utf-8")
    lines = _strip_frontmatter(text.splitlines())
    relative_path = path.relative_to(vault).as_posix()
    title = path.stem
    chunks: list[MarkdownChunk] = []
    heading_stack: list[tuple[int, str]] = []
    current_lines: list[str] = []
    current_heading = "Introduction"

    def flush() -> None:
        content = "\n".join(current_lines).strip()
        if not content:
            return
        chunks.append(
            MarkdownChunk(
                path=relative_path,
                title=title,
                heading=current_heading,
                content=content,
                ordinal=len(chunks),
            )
        )

    for line in lines:
        match = HEADING_RE.match(line)
        if not match:
            current_lines.append(line)
            continue

        flush()
        current_lines = []
        level = len(match.group(1))
        heading_text = match.group(2).strip().strip("#").strip()
        if level == 1 and heading_text:
            title = heading_text
        heading_stack = [item for item in heading_stack if item[0] < level]
        heading_stack.append((level, heading_text))
        current_heading = " > ".join(item[1] for item in heading_stack)

    flush()
    return chunks

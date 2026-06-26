"""Loads raw documents from the Obsidian vault."""

import re
from pathlib import Path

import structlog

from rag.ingestion.types import Document, DocumentMetadata

logger = structlog.get_logger()

_WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
_H1_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def load_vault(vault_path: Path) -> list[Document]:
    """Recursively load all markdown documents from the vault, skipping README.md."""
    documents: list[Document] = []
    for source in sorted(vault_path.rglob("*.md")):
        if source.name.lower() == "readme.md":
            continue
        try:
            content = source.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("failed_to_read_document", source=str(source), error=str(exc))
            continue
        documents.append(
            Document(
                content=content,
                metadata=DocumentMetadata(
                    source=source,
                    title=_extract_title(content, source),
                    word_count=len(content.split()),
                    wikilinks=_extract_wikilinks(content),
                ),
            )
        )
    return documents


def _extract_title(content: str, source: Path) -> str:
    match = _H1_PATTERN.search(content)
    if match:
        return match.group(1).strip()
    return source.stem.replace("-", " ").title()


def _extract_wikilinks(content: str) -> list[str]:
    targets = {match.group(1).strip() for match in _WIKILINK_PATTERN.finditer(content)}
    return sorted(targets)

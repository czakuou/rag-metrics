"""Tests for rag.ingestion.loader."""

import sys
from pathlib import Path

import pytest
import structlog

from rag.ingestion.loader import load_vault


def test_load_vault_returns_one_document_per_markdown_file(tmp_path: Path) -> None:
    # Given
    (tmp_path / "a.md").write_text("# A\nContent A")
    (tmp_path / "b.md").write_text("# B\nContent B")

    # When
    documents = load_vault(tmp_path)

    # Then
    assert len(documents) == 2


def test_load_vault_skips_readme(tmp_path: Path) -> None:
    # Given
    (tmp_path / "README.md").write_text("# Vault index")
    (tmp_path / "note.md").write_text("# Note\nContent")

    # When
    documents = load_vault(tmp_path)

    # Then
    assert len(documents) == 1
    assert documents[0].metadata.source.name == "note.md"


def test_load_vault_extracts_title_from_h1_heading(tmp_path: Path) -> None:
    # Given
    (tmp_path / "note.md").write_text("# My Great Title\nSome content")

    # When
    [document] = load_vault(tmp_path)

    # Then
    assert document.metadata.title == "My Great Title"


def test_load_vault_falls_back_to_filename_when_no_h1(tmp_path: Path) -> None:
    # Given
    (tmp_path / "cap-theorem.md").write_text("Some content without a heading")

    # When
    [document] = load_vault(tmp_path)

    # Then
    assert document.metadata.title == "Cap Theorem"


def test_load_vault_extracts_wikilinks(tmp_path: Path) -> None:
    # Given
    (tmp_path / "note.md").write_text("# Note\nSee [[Other Note]] and [[Another]].")

    # When
    [document] = load_vault(tmp_path)

    # Then
    assert document.metadata.wikilinks == ["Another", "Other Note"]


def test_load_vault_extracts_target_from_aliased_wikilinks(tmp_path: Path) -> None:
    # Given
    (tmp_path / "note.md").write_text("# Note\nSee [[Real Title|alias text]].")

    # When
    [document] = load_vault(tmp_path)

    # Then
    assert document.metadata.wikilinks == ["Real Title"]


@pytest.mark.skipif(sys.platform == "win32", reason="chmod permissions not meaningful on Windows")
def test_load_vault_continues_and_logs_warning_when_file_is_unreadable(
    tmp_path: Path,
) -> None:
    # Given
    unreadable = tmp_path / "secret.md"
    unreadable.write_text("# Secret\nContent")
    unreadable.chmod(0o000)
    (tmp_path / "readable.md").write_text("# Readable\nContent")

    log_output: list[dict[str, object]] = []

    def _capture(
        _logger: object, _method_name: str, event_dict: dict[str, object]
    ) -> dict[str, object]:
        log_output.append(event_dict)
        raise structlog.DropEvent

    structlog.configure(processors=[_capture])

    try:
        # When
        documents = load_vault(tmp_path)

        # Then
        assert len(documents) == 1
        assert documents[0].metadata.source.name == "readable.md"
        assert any(entry.get("event") == "failed_to_read_document" for entry in log_output)
    finally:
        unreadable.chmod(0o644)
        structlog.reset_defaults()

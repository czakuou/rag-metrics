"""Tests for rag.shared.cli."""

from rag.shared.cli import render_table


def test_render_table_includes_all_headers_and_row_values() -> None:
    # Given
    headers = ["Metric", "Score"]
    rows = [["faithfulness", "0.9000"], ["answer_relevancy", "0.8000"]]

    # When
    table = render_table(headers, rows)

    # Then
    assert "Metric" in table
    assert "Score" in table
    assert "faithfulness" in table
    assert "0.9000" in table
    assert "answer_relevancy" in table


def test_render_table_pads_columns_to_widest_cell() -> None:
    # Given
    headers = ["Name"]
    rows = [["short"], ["a much longer value"]]

    # When
    table = render_table(headers, rows)
    lines = table.splitlines()

    # Then
    content_lines = [line for line in lines if not line.startswith("|-")]
    widths = {len(line) for line in content_lines}
    assert len(widths) == 1

"""Plain-text table rendering for CLI output. No external dependency, no print()."""


def render_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows)) if rows else len(headers[i])
        for i in range(len(headers))
    ]
    separator = "|" + "|".join("-" * (width + 2) for width in widths) + "|"

    def render_row(cells: list[str]) -> str:
        padded = (cell.ljust(width) for cell, width in zip(cells, widths, strict=True))
        return "| " + " | ".join(padded) + " |"

    lines = [separator, render_row(headers), separator]
    lines.extend(render_row(row) for row in rows)
    lines.append(separator)
    return "\n".join(lines)

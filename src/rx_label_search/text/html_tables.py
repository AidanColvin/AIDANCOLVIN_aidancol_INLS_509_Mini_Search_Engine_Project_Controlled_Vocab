"""Pure parsing of openFDA HTML table strings with the standard library parser."""

from __future__ import annotations

from html.parser import HTMLParser

CELL_TAGS = frozenset({"td", "th"})


class TableCollector(HTMLParser):
    """Collects every table in an HTML fragment as rows of cell text."""

    def __init__(self) -> None:
        """
        Takes no arguments.
        Initializes the parser state with no tables, rows, or open cell.
        Gives nothing.
        """
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.current_rows: list[list[str]] | None = None
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """
        Takes a tag name and its attributes.
        Opens a table, a row, or a cell depending on the tag.
        Gives nothing.
        """
        if tag == "table":
            self.current_rows = []
        elif tag == "tr" and self.current_rows is not None:
            self.current_row = []
        elif tag in CELL_TAGS and self.current_row is not None:
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        """
        Takes a tag name.
        Closes the matching cell, row, or table and stores its content.
        Gives nothing.
        """
        if tag in CELL_TAGS and self.current_cell is not None and self.current_row is not None:
            self.current_row.append(" ".join("".join(self.current_cell).split()))
            self.current_cell = None
        elif tag == "tr" and self.current_row is not None and self.current_rows is not None:
            self.current_rows.append(self.current_row)
            self.current_row = None
        elif tag == "table" and self.current_rows is not None:
            self.tables.append(self.current_rows)
            self.current_rows = None

    def handle_data(self, data: str) -> None:
        """
        Takes a run of text inside the fragment.
        Appends it to the open cell when there is one.
        Gives nothing.
        """
        if self.current_cell is not None:
            self.current_cell.append(data)


def parse_tables(html: str) -> tuple[tuple[tuple[str, ...], ...], ...]:
    """
    Takes an HTML fragment that may contain tables.
    Parses every table into rows of cell text with whitespace collapsed.
    Gives a tuple of tables, each a tuple of rows, empty when the fragment has no tables.
    """
    collector = TableCollector()
    collector.feed(html)
    collector.close()
    return tuple(tuple(tuple(row) for row in table) for table in collector.tables)


def strip_tags(html: str) -> str:
    """
    Takes an HTML fragment.
    Removes every tag and collapses whitespace in the remaining text.
    Gives the plain text, empty for an empty fragment.
    """
    collector = TableCollector()
    pieces: list[str] = []
    collector.handle_data = pieces.append  # type: ignore[method-assign]
    collector.feed(html)
    collector.close()
    return " ".join("".join(pieces).split())

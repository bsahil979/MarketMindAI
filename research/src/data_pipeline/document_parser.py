import re
import html
from pathlib import Path
from typing import Dict, Any, Tuple
from bs4 import BeautifulSoup, NavigableString, Tag

class DocumentParser:
    """
    Parser for financial documents (HTML / SEC Filings / Plain Text).
    Extracts text while preserving Markdown table formatting for numerical analysis.
    """

    def __init__(self, processed_dir: str = "research/dataset/processed"):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def parse_file(self, file_path: Path) -> Tuple[str, str]:
        """
        Parses a single filing file (HTML/TXT) and saves clean markdown text.
        Returns a tuple of (document_id, clean_text).
        """
        doc_id = file_path.stem
        raw_content = file_path.read_text(encoding="utf-8", errors="ignore")

        if "<html" in raw_content.lower() or "<table" in raw_content.lower():
            clean_text = self._parse_html(raw_content)
        else:
            clean_text = self._clean_plain_text(raw_content)

        output_file = self.processed_dir / f"{doc_id}.md"
        output_file.write_text(clean_text, encoding="utf-8")

        return doc_id, clean_text

    def _parse_html(self, html_content: str) -> str:
        """
        Parses HTML filing content, preserving tables as Markdown tables.
        """
        soup = BeautifulSoup(html_content, "lxml")

        # Remove irrelevant tags
        for tag in soup(["script", "style", "head", "noscript", "meta"]):
            tag.decompose()

        # Convert <table> tags to Markdown tables
        for table in soup.find_all("table"):
            md_table = self._table_to_markdown(table)
            table.replace_with(soup.new_string(f"\n\n{md_table}\n\n"))

        # Extract text content
        text = soup.get_text(separator="\n")
        return self._clean_plain_text(text)

    def _table_to_markdown(self, table_tag: Tag) -> str:
        """
        Converts an HTML <table> element to a Markdown table string.
        """
        rows = []
        for tr in table_tag.find_all("tr"):
            cells = [re.sub(r"\s+", " ", cell.get_text(strip=True)) for cell in tr.find_all(["td", "th"])]
            # Filter out empty spacer cells
            filtered = [c for c in cells if c]
            if filtered:
                rows.append(filtered)

        if not rows:
            return ""

        max_cols = max(len(r) for r in rows)
        md_lines = []

        # Header row
        header = rows[0] + [""] * (max_cols - len(rows[0]))
        md_lines.append("| " + " | ".join(header) + " |")
        md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")

        # Data rows
        for row in rows[1:]:
            padded = row + [""] * (max_cols - len(row))
            md_lines.append("| " + " | ".join(padded) + " |")

        return "\n".join(md_lines)

    def _clean_plain_text(self, text: str) -> str:
        """
        Normalizes whitespace, unescapes entities, and cleans text formatting.
        """
        text = html.unescape(text)
        # Replace multiple spaces/newlines while preserving table lines
        lines = text.splitlines()
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                cleaned_lines.append(stripped)

        return "\n".join(cleaned_lines)

if __name__ == "__main__":
    parser = DocumentParser()
    print("DocumentParser ready.")

"""
Streaming GEDCOM 5.5.1 / 7.0 Parser.
Robust line tokenizer, hierarchy builder, and multi-encoding handler.
"""

import re
from typing import List, Optional, Callable, Generator
from src.gedcom.structure import GedcomLine, GedcomRecord


class GedcomParser:
    def __init__(self, progress_callback: Optional[Callable[[float, str], None]] = None):
        self.progress_callback = progress_callback

    def parse_line(self, line: str) -> Optional[GedcomLine]:
        """Parses a single GEDCOM syntax line into a GedcomLine object."""
        clean = line.strip("\r\n")
        if not clean:
            return None

        # Regex pattern: level [xref] tag [value]
        # Example: 0 @I123@ INDI
        # Example: 1 NAME Jan /Kowalski/
        pattern = r"^(\d+)\s+(?:(@[^@]+@)\s+)?([A-Z0-9_]+)(?:\s+(.*))?$"
        match = re.match(pattern, clean)
        if not match:
            return None

        level = int(match.group(1))
        xref = match.group(2)
        tag = match.group(3)
        value = match.group(4)

        return GedcomLine(level=level, tag=tag, xref=xref, value=value, raw_line=clean)

    def parse_string(self, content: str) -> List[GedcomRecord]:
        """Parses full GEDCOM text content into a tree of top-level GedcomRecords."""
        lines = content.splitlines()
        return self._build_record_tree(lines)

    def parse_file(self, file_path: str) -> List[GedcomRecord]:
        """Reads and parses a GEDCOM file, automatically detecting UTF-8, ANSEL, CP1250, Latin1 encodings."""
        from src.gedcom.encoding import detect_and_read_gedcom
        content = detect_and_read_gedcom(file_path)
        return self.parse_string(content)

    def _build_record_tree(self, lines: List[str]) -> List[GedcomRecord]:
        top_records: List[GedcomRecord] = []
        stack: List[tuple[int, GedcomRecord]] = []
        total_lines = len(lines)

        for idx, raw_line in enumerate(lines):
            if self.progress_callback and total_lines > 0 and idx % 1000 == 0:
                self.progress_callback(idx / total_lines, f"Parsowanie wiersza {idx}/{total_lines}")

            line_obj = self.parse_line(raw_line)
            if not line_obj:
                continue

            rec = GedcomRecord(tag=line_obj.tag, xref=line_obj.xref, value=line_obj.value)

            if line_obj.level == 0:
                top_records.append(rec)
                stack = [(0, rec)]
            else:
                # Pop stack until we find parent at level - 1
                while stack and stack[-1][0] >= line_obj.level:
                    stack.pop()

                if stack:
                    parent_rec = stack[-1][1]
                    parent_rec.sub_records.append(rec)

                stack.append((line_obj.level, rec))

        if self.progress_callback:
            self.progress_callback(1.0, "Parsowanie zakończone")

        return top_records

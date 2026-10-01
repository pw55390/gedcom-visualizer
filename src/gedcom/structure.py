"""
GEDCOM Data Structures and Tag Definitions (GEDCOM 5.5.1 and 7.0).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class GedcomLine:
    level: int
    tag: str
    xref: Optional[str] = None
    value: Optional[str] = None
    raw_line: str = ""


@dataclass
class GedcomRecord:
    tag: str
    xref: Optional[str] = None
    value: Optional[str] = None
    sub_records: List["GedcomRecord"] = field(default_factory=list)

    def get_sub_records(self, tag: str) -> List["GedcomRecord"]:
        """Returns all direct child sub-records matching the given tag."""
        return [rec for rec in self.sub_records if rec.tag == tag]

    def get_sub_value(self, tag: str) -> Optional[str]:
        """Returns value of the first matching child sub-record."""
        sub = self.get_sub_records(tag)
        return sub[0].value if sub else None

    def get_full_value(self) -> str:
        """Assembles full text value handling CONC (concatenation) and CONT (continuation) lines."""
        text_parts = [self.value] if self.value else []
        for sub in self.sub_records:
            if sub.tag == "CONC":
                if sub.value:
                    if text_parts:
                        text_parts[-1] += sub.value
                    else:
                        text_parts.append(sub.value)
            elif sub.tag == "CONT":
                text_parts.append("\n" + (sub.value or ""))
        return "".join(text_parts)

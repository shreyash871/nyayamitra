"""BNS <-> IPC cross-era bridge.

Given a section reference from either era, return every tag that should be
included in a search so results span both statutory periods.
"""

import re
from sqlalchemy.orm import Session

from app.models import BnsMapping

# Matches "IPC 420", "Section 302 IPC", "BNS 318(4)", "u/s 498A"
SECTION_PATTERN = re.compile(
    r"(?:(IPC|BNS)\s*)?(?:section\s*|sec\.?\s*|u/s\s*)?(\d+[A-Z]?(?:\(\d+\))?)\s*(?:(IPC|BNS))?",
    re.IGNORECASE,
)


def to_tag(section: str, era: str) -> str:
    cleaned = section.replace("(", "_").replace(")", "").strip().upper()
    return f"{era.upper()}_{cleaned}"


def lookup(db: Session, tag: str) -> BnsMapping | None:
    """Find the mapping row containing this tag, from either side."""
    return (
        db.query(BnsMapping)
        .filter((BnsMapping.ipc_section == tag) | (BnsMapping.bns_section == tag))
        .first()
    )


def expand(db: Session, tag: str) -> list[str]:
    """'IPC_420' -> ['IPC_420', 'BNS_318_4']. Unknown tag -> [tag] unchanged."""
    row = lookup(db, tag)
    if row is None:
        return [tag]
    return [t for t in (row.ipc_section, row.bns_section) if t]


def extract_sections(text: str) -> list[str]:
    """Pull every section reference out of free text and return them as tags."""
    tags: list[str] = []
    for match in SECTION_PATTERN.finditer(text):
        prefix, number, suffix = match.groups()
        era = prefix or suffix
        if era is None:
            continue  # a bare number with no era is too ambiguous to trust
        tags.append(to_tag(number, era))
    return list(dict.fromkeys(tags))  # de-duplicate, preserve order


def expand_query(db: Session, text: str) -> list[str]:
    """Full pipeline: free text -> all cross-era section tags to search on."""
    expanded: list[str] = []
    for tag in extract_sections(text):
        expanded.extend(expand(db, tag))
    return list(dict.fromkeys(expanded))

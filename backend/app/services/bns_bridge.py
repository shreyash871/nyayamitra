"""BNS <-> IPC cross-era bridge.

Given a section reference from either era, return every tag that should be
included in a search so results span both statutory periods.
"""

import re

from sqlalchemy.orm import Session

from app.models import BnsMapping

# Judgment prose: "punishable under Sections 120B, 420, 379 of the Indian Penal Code"
SECTION_LIST = re.compile(
    r"(?:under\s+)?(?:Sections?|Secs?\.?|u/s)\s+"
    r"([0-9A-Z,\s\-()]{1,80}?)"
    r"\s+(?:of\s+the\s+)?"
    r"(IPC|Indian Penal Code|BNS|Bharatiya Nyaya Sanhita)",
    re.IGNORECASE,
)

# User queries: "IPC 420", "BNS 318(4)", "BNS 103 murder"
ERA_FIRST = re.compile(
    r"\b(IPC|BNS)\s+(?:sections?\s+|secs?\.?\s+)?(\d{1,3}[A-Z]{0,2}(?:\(\d+\))?)",
    re.IGNORECASE,
)

SINGLE_NUM = re.compile(r"\b(\d{1,3}[A-Z]{0,2})\b")

ERA_ALIASES = {
    "ipc": "IPC",
    "indian penal code": "IPC",
    "bns": "BNS",
    "bharatiya nyaya sanhita": "BNS",
}


def to_tag(section: str, era: str) -> str:
    """'318(4)', 'BNS' -> 'BNS_318_4'"""
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
    """'IPC_420' -> ['IPC_420', 'BNS_318_4']. Unknown tag -> [tag] unchanged.

    Falls back to prefix matching so a bare section ('BNS_318') resolves
    against sub-section rows ('BNS_318_1', 'BNS_318_4') - users cite the
    section, the table stores the sub-section.
    """
    row = lookup(db, tag)
    if row is not None:
        return [t for t in (row.ipc_section, row.bns_section) if t]

    # Bare section: match any sub-section row beginning with this tag
    rows = (
        db.query(BnsMapping)
        .filter(
            (BnsMapping.ipc_section.like(f"{tag}\\_%", escape="\\"))
            | (BnsMapping.bns_section.like(f"{tag}\\_%", escape="\\"))
        )
        .all()
    )
    if not rows:
        return [tag]

    out = [tag]
    for r in rows:
        out.extend(t for t in (r.ipc_section, r.bns_section) if t)
    return list(dict.fromkeys(out))


def extract_sections(text: str) -> list[str]:
    """Pull section references out of free text and return them as tags.

    Two passes: judgment prose ("under Sections 120B, 420 of the IPC")
    and query phrasing ("IPC 420"). Only fires when an era marker is
    present - a bare number is too ambiguous to attribute to a statute.
    """
    tags: list[str] = []

    for match in SECTION_LIST.finditer(text):
        numbers, era_raw = match.group(1), match.group(2).lower()
        era = ERA_ALIASES.get(era_raw)
        if not era:
            continue
        for num in SINGLE_NUM.findall(numbers):
            tags.append(to_tag(num, era))

    for match in ERA_FIRST.finditer(text):
        era, num = match.group(1).upper(), match.group(2)
        tags.append(to_tag(num, era))

    return list(dict.fromkeys(tags))


def expand_query(db: Session, text: str) -> list[str]:
    """Full pipeline: free text -> all cross-era section tags to search on."""
    expanded: list[str] = []
    for tag in extract_sections(text):
        expanded.extend(expand(db, tag))
    return list(dict.fromkeys(expanded))

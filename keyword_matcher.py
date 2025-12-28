import re
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class KeywordHit:
    keyword: str
    where: str  # title|snippet|link


# Exclusions to reduce false positives (cosmetics, generic language)
EXCLUSION_PATTERNS = [
    re.compile(r"\bfine\s+line(s)?\b", re.IGNORECASE),
    re.compile(r"\bwrinkle(s)?\b", re.IGNORECASE),
    re.compile(r"\bskin\s+care\b", re.IGNORECASE),
]

# Keywords (keep them tight; use word boundaries)
NEGATIVE_PATTERNS = [
    # Regulatory / enforcement
    (r"\bsanction(s)?\b", "sanction"),
    (r"\bfine(s)?\b", "fine"),
    (r"\bpenalt(y|ies)\b", "penalty"),
    (r"\bcease\s+and\s+desist\b", "cease and desist"),
    (r"\benforcement\b", "enforcement"),
    (r"\bregulator(y)?\b", "regulatory"),

    # Legal / dispute
    (r"\blawsuit(s)?\b", "lawsuit"),
    (r"\bclass\s+action\b", "class action"),
    (r"\ballegation(s)?\b", "allegations"),
    (r"\bfraud\b", "fraud"),
    (r"\bscam(s)?\b", "scam"),
    (r"\bindictment(s)?\b", "indictment"),
    (r"\bcharged\b", "charged"),
    (r"\barrest(ed)?\b", "arrest"),

    # Business distress
    (r"\bbankrupt(cy|cies)\b", "bankruptcy"),
    (r"\binsolvenc(y|ies)\b", "insolvency"),
    (r"\bshutdown\b", "shutdown"),
    (r"\bliquidation\b", "liquidation"),
    (r"\badministration\b", "administration"),
]

COMPILED = [(re.compile(p, re.IGNORECASE), label) for p, label in NEGATIVE_PATTERNS]


def _is_excluded(text: str) -> bool:
    return any(rx.search(text) for rx in EXCLUSION_PATTERNS)


def find_negative_hits(title: str, snippet: str, link: str) -> List[KeywordHit]:
    hits: List[KeywordHit] = []
    title = title or ""
    snippet = snippet or ""
    link = link or ""

    blob_title = title.strip()
    blob_snip = snippet.strip()

    # exclusions apply only to generic snippets
    if _is_excluded(blob_snip):
        # still allow strong words like fraud/arrest if present
        # but block "fine" specifically from cosmetics contexts
        pass

    for rx, label in COMPILED:
        if rx.search(blob_title):
            if label == "fine" and _is_excluded(blob_title):
                continue
            hits.append(KeywordHit(keyword=label, where="title"))
        if rx.search(blob_snip):
            if label == "fine" and _is_excluded(blob_snip):
                continue
            hits.append(KeywordHit(keyword=label, where="snippet"))

    return hits
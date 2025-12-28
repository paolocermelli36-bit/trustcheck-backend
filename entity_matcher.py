import re
from typing import List


LEGAL_TOKENS = {
    "s.p.a", "spa", "srl", "s.r.l", "s.a", "sa", "ltd", "plc", "inc", "llc", "gmbh",
    "ag", "bv", "b.v", "nv", "n.v", "kg", "pte", "pte.", "co", "company",
}

STOP_TOKENS = {"the", "and", "&", "of", "for", "a", "an", "de", "di", "del", "della", "dei"}


def _norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _tokens(s: str) -> List[str]:
    return [t for t in _norm(s).split() if t]


def person_match(query: str, text: str) -> bool:
    q = _tokens(query)
    if len(q) < 2:
        return False
    first, last = q[0], q[-1]
    t = _norm(text)
    # strict: first and last must appear (not necessarily adjacent, but both)
    return (first in t) and (last in t)


def company_match(query: str, text: str) -> bool:
    q = _tokens(query)
    if not q:
        return False

    # drop legal/stop tokens
    core = [t for t in q if t not in LEGAL_TOKENS and t not in STOP_TOKENS and len(t) >= 3]
    if not core:
        # fallback: at least one token from original query
        core = [t for t in q if len(t) >= 3]

    t = _norm(text)
    hits = sum(1 for tok in core if tok in t)

    # If query has multiple meaningful tokens -> require at least 2 hits
    if len(core) >= 2:
        return hits >= 2
    return hits >= 1


def entity_match(query: str, text: str) -> bool:
    qn = _norm(query)
    parts = [p for p in qn.split() if p]
    if any(p in LEGAL_TOKENS for p in parts):
        return company_match(query, text)

    # if it looks like "Nome Cognome"
    if len(parts) >= 2 and all(len(p) >= 2 for p in parts):
        return person_match(query, text)

    return company_match(query, text)
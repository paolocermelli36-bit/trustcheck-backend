import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple

@dataclass(frozen=True)
class KeywordHit:
    keyword: str
    where: str  # title|snippet

BASE_DIR = Path(__file__).resolve().parent
NEG_FILE = BASE_DIR / "queries" / "negative_queries.json"

EXCLUSION_PATTERNS = [
    re.compile(r"\bfine\s+line(s)?\b", re.IGNORECASE),
    re.compile(r"\bwrinkle(s)?\b", re.IGNORECASE),
    re.compile(r"\bskin\s+care\b", re.IGNORECASE),
]

def _is_excluded(text: str) -> bool:
    return any(rx.search(text or "") for rx in EXCLUSION_PATTERNS)

def _compile_terms(terms: List[str]) -> List[Tuple[re.Pattern, str]]:
    compiled: List[Tuple[re.Pattern, str]] = []
    for term in terms:
        t = (term or "").strip()
        if not t:
            continue
        if " " in t:
            pattern = re.escape(t).replace("\\ ", r"\s+")
        else:
            pattern = r"\b" + re.escape(t) + r"\b"
        compiled.append((re.compile(pattern, re.IGNORECASE), t))
    return compiled

def _load_negative_terms() -> Dict[str, List[str]]:
    if not NEG_FILE.exists():
        raise FileNotFoundError(f"Missing negative terms file: {NEG_FILE}")
    data = json.loads(NEG_FILE.read_text(encoding="utf-8"))
    out: Dict[str, List[str]] = {}
    for k in ("en", "it"):
        v = data.get(k, [])
        if isinstance(v, list):
            out[k] = [str(x) for x in v]
    if not out:
        raise ValueError("negative_queries.json has no usable terms.")
    return out

_TERMS = _load_negative_terms()
_COMPILED = {lang: _compile_terms(terms) for lang, terms in _TERMS.items()}

def find_negative_hits(title: str, snippet: str, language: str = "en") -> List[KeywordHit]:
    lang = "it" if (language or "").lower().startswith("it") else "en"
    compiled = _COMPILED.get(lang) or _COMPILED.get("en") or []

    t = title or ""
    s = snippet or ""

    excluded_title = _is_excluded(t)
    excluded_snip = _is_excluded(s)

    hits: List[KeywordHit] = []
    for rx, label in compiled:
        if rx.search(t):
            if excluded_title and label == "fine":
                continue
            hits.append(KeywordHit(keyword=label, where="title"))
        if rx.search(s):
            if excluded_snip and label == "fine":
                continue
            hits.append(KeywordHit(keyword=label, where="snippet"))
    return hits
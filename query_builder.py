import json
from pathlib import Path
from typing import List, Dict

BASE_DIR = Path(__file__).resolve().parent

def _load_patterns(language: str) -> List[str]:
    fname = "queriesenglish_queries.json" if language.lower().startswith("en") else "queriesitalian_queries.json"
    path = BASE_DIR / fname
    if not path.exists():
        raise FileNotFoundError(f"Missing query patterns file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    patterns = data.get("patterns") or []
    if not isinstance(patterns, list) or not patterns:
        raise ValueError(f"Invalid patterns in {path}")
    return patterns

def build_queries(name: str, language: str) -> List[Dict[str, str]]:
    patterns = _load_patterns(language)
    name = (name or "").strip()

    out: List[Dict[str, str]] = []
    seen = set()

    for i, pat in enumerate(patterns, start=1):
        q = (pat or "").replace("{name}", name).strip()
        if not q:
            continue
        key = q.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"id": f"Q{i}", "q": q})

    return out
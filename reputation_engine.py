from typing import Dict, Any, List

from entity_matcher import entity_match
from keyword_matcher import find_negative_hits


def analyze(query: str, google_results: Dict[str, Any]) -> Dict[str, Any]:
    items = google_results.get("items", []) or []

    analyzed_results: List[Dict[str, Any]] = []
    adverse_count = 0

    for item in items:
        title = item.get("title", "") or ""
        snippet = item.get("snippet", "") or ""
        link = item.get("link", "") or ""

        text_blob = f"{title} {snippet} {link}"
        relevant = entity_match(query, text_blob)

        hits = find_negative_hits(title, snippet, link) if relevant else []
        is_negative = relevant and len(hits) > 0

        if is_negative:
            adverse_count += 1

        analyzed_results.append({
            "title": title,
            "snippet": snippet,
            "link": link,
            "source": item.get("displayLink", ""),
            "position": item.get("rank") or item.get("position") or None,
            "isNegative": bool(is_negative),
            "relevant": bool(relevant),
            "negativeHits": [f"{h.keyword}:{h.where}" for h in hits],
        })

    return {
        "query": query,
        "totalAnalyzed": len(analyzed_results),
        "adverseCount": adverse_count,
        "results": analyzed_results,
    }
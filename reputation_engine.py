from typing import Dict, Any, List
from entity_matcher import entity_match
from keyword_matcher import find_negative_hits

def analyze(input_query: str, google_items: List[Dict[str, Any]], language: str = "en") -> Dict[str, Any]:
    analyzed: List[Dict[str, Any]] = []
    adverse_count = 0

    for item in google_items:
        title = item.get("title", "") or ""
        snippet = item.get("snippet", "") or ""
        link = item.get("link", "") or ""
        source = item.get("displayLink", "") or item.get("source", "") or ""

        relevant = entity_match(input_query, f"{title} {snippet} {link} {source}")
        hits = find_negative_hits(title, snippet, language=language)
        is_negative = bool(relevant and hits)

        if is_negative:
            adverse_count += 1
            analyzed.append({
                "title": title,
                "snippet": snippet,
                "link": link,
                "source": source,
                "position": item.get("rank") or item.get("position") or None,
                "isNegative": True,
                "relevant": True,
                "negativeHits": [f"{h.keyword}:{h.where}" for h in hits],
                "queryHits": sorted(list(set(item.get("_qhits", []) or []))),
            })

    return {
        "query": input_query,
        "totalAnalyzed": len(google_items),
        "adverseCount": adverse_count,
        "results": analyzed
    }
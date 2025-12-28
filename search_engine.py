import requests
from typing import Dict, Any

from config import GOOGLE_API_KEY, GOOGLE_CX_ID


class GoogleSearchError(RuntimeError):
    pass


def google_search(query: str, start_index: int = 1, num_results: int = 10) -> Dict[str, Any]:
    """
    Google Custom Search JSON API.
    start_index is 1-based. num_results max is 10.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CX_ID:
        raise GoogleSearchError("Missing GOOGLE_API_KEY or GOOGLE_CX_ID")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX_ID,
        "q": query,
        "start": start_index,
        "num": max(1, min(10, int(num_results))),
    }

    resp = requests.get(url, params=params, timeout=20)
    if resp.status_code != 200:
        raise GoogleSearchError(f"Google API error {resp.status_code}: {resp.text[:400]}")
    return resp.json()
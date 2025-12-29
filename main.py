from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from config import DEFAULT_MAX_RESULTS, RATE_LIMIT_RPM, MAX_RESULTS_PER_QUERY
from search_engine import google_search, GoogleSearchError
from reputation_engine import analyze
from query_builder import build_queries

import time

app = FastAPI(title="TrustCheck Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_last_call_ts = 0.0

class AnalyzeRequest(BaseModel):
    query: str
    language: str | None = None

def _rate_limit():
    global _last_call_ts
    now = time.time()
    min_interval = 60.0 / max(1, RATE_LIMIT_RPM)
    if now - _last_call_ts < min_interval:
        time.sleep(min_interval - (now - _last_call_ts))
    _last_call_ts = time.time()

@app.get("/")
def root():
    return {"status":"ok","service":"TrustCheck Turbo Engine 2.1"}

@app.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest):
    q = (req.query or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Missing query")

    lang = (req.language or "en").strip().lower()
    lang = "it" if lang.startswith("it") else "en"

    max_results = max(10, min(int(DEFAULT_MAX_RESULTS), 100))
    subqueries = build_queries(q, lang) or [{"id": "Q1", "q": q}]

    by_link = {}  # link -> item (with _qhits)

    for sq in subqueries:
        if len(by_link) >= max_results:
            break

        per_q_cap = max(10, min(int(MAX_RESULTS_PER_QUERY), 50))
        start = 1
        fetched = 0

        while fetched < per_q_cap and len(by_link) < max_results:
            _rate_limit()
            try:
                data = google_search(sq["q"], start_index=start, num_results=10)
            except GoogleSearchError as e:
                raise HTTPException(status_code=502, detail=str(e))

            batch = data.get("items", []) or []
            if not batch:
                break

            for item in batch:
                link = (item.get("link") or "").strip()
                if not link:
                    continue

                if link in by_link:
                    by_link[link].setdefault("_qhits", [])
                    by_link[link]["_qhits"].append(sq["id"])
                    continue

                item["_qhits"] = [sq["id"]]
                by_link[link] = item

                if len(by_link) >= max_results:
                    break

            fetched += len(batch)
            start += 10
            if start > 100:
                break

    collected = list(by_link.values())[:max_results]
    return analyze(q, collected, language=lang)
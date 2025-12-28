import os
import time
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---- optional: your classifier (can be dumb for now) ----
try:
    from risk_classifier import classify_result  # expects dict -> dict with risk_level
except Exception:
    classify_result = None

app = FastAPI(title="TrustCheck API", version="3.4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    query: str

def env_bool(name: str, default: str = "0") -> bool:
    return str(os.getenv(name, default)).strip() in ("1", "true", "True", "yes", "YES")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
GOOGLE_CSE_CX = os.getenv("GOOGLE_CSE_CX", "").strip()

TC_MAX_RESULTS = int(os.getenv("TC_MAX_RESULTS", "30"))  # we will set to 100 later
TC_DEBUG = env_bool("TC_DEBUG", "1")  # default ON for now

def google_cse_fetch(query: str, max_results: int = 30) -> List[Dict[str, Any]]:
    """
    Fetch up to max_results (<=100) using Google Custom Search JSON API.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_CX:
        if TC_DEBUG:
            print("[TC] MISSING GOOGLE_API_KEY or GOOGLE_CSE_CX")
        return []

    items: List[Dict[str, Any]] = []
    start = 1
    # Google CSE returns max 10 per request
    while len(items) < max_results and start <= 91:
        num = min(10, max_results - len(items))
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_CX,
            "q": query,
            "num": num,
            "start": start,
        }
        t0 = time.time()
        r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=20)
        ms = int((time.time() - t0) * 1000)

        if TC_DEBUG:
            print(f"[TC] Google fetch start={start} num={num} status={r.status_code} ms={ms}")

        if r.status_code != 200:
            if TC_DEBUG:
                print("[TC] Google error body:", r.text[:500])
            break

        data = r.json() or {}
        batch = data.get("items") or []
        if TC_DEBUG:
            print(f"[TC] items returned in batch: {len(batch)}")

        if not batch:
            break

        for it in batch:
            link = it.get("link") or ""
            title = it.get("title") or ""
            snippet = it.get("snippet") or ""
            display = it.get("displayLink") or ""
            items.append({
                "title": title,
                "snippet": snippet,
                "link": link,
                "source": display,
                "position": len(items) + 1,
            })

        start += 10

    return items

@app.get("/health")
def health():
    return {
        "ok": True,
        "version": "3.4",
        "google_key_set": bool(GOOGLE_API_KEY),
        "google_cx_set": bool(GOOGLE_CSE_CX),
        "max_results": TC_MAX_RESULTS,
        "debug": TC_DEBUG,
    }

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    q = (req.query or "").strip()
    t0 = time.time()

    if TC_DEBUG:
        print(f"\n[TC] /analyze query={q!r} max_results={TC_MAX_RESULTS}")

    raw = google_cse_fetch(q, max_results=TC_MAX_RESULTS)

    if TC_DEBUG:
        print(f"[TC] raw_results={len(raw)}")

    results: List[Dict[str, Any]] = []
    negative = 0

    for r in raw:
        # default: not negative
        is_neg = False
        risk_obj: Dict[str, Any] = {}

        if classify_result:
            risk_obj = classify_result(r) or {}
            is_neg = (risk_obj.get("risk_level") == "high")

        out = {
            **r,
            "is_negative": bool(is_neg),
            "severity": "high" if is_neg else "none",
            "is_authority_or_regulator": False,
            "risk": risk_obj,
            "subject_mode": "unknown",
        }
        results.append(out)
        if is_neg:
            negative += 1

    elapsed_ms = int((time.time() - t0) * 1000)

    if TC_DEBUG:
        print(f"[TC] returning total_results={len(results)} negative_results={negative} elapsed_ms={elapsed_ms}")

    return {
        "query": q,
        "subject_mode": "unknown",
        "total_results": len(results),
        "negative_results": negative,
        "elapsed_ms": elapsed_ms,
        "results": results,  # IMPORTANT: returns ALL, no filtering
    }
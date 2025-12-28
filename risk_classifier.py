import re
from typing import Any, Dict, List, Optional

# -------------------------------------------------------------------
# TRUSTCHECK vE1 (EVENT ENGINE) — BINARY
# OUTPUT ONLY IF AN "EVENT OF RISK" IS DETECTED.
#
# Risk event types:
# - authority (regulator / authority measures, decisions, sanctions)
# - judicial  (arrest, indictment, trial, conviction, seizure, bankruptcy filings)
# - class_action (class action / collective redress)
#
# Everything else -> NONE (no signal)
# -------------------------------------------------------------------

# Authorities / regulators (expandable, but keep tight)
AUTHORITY_KEYWORDS = [
    # Italy
    "banca d'italia", "bank of italy", "consob", "ivass", "agcm", "antitrust",
    "gdf", "guardia di finanza", "procura", "tribunale", "corte d'appello",
    "gazzetta ufficiale",
    # EU/UK/US common
    "fca", "finma", "amf", "acpr", "cssf", "bafin", "cbI", "central bank",
    "sec", "finra", "doj", "fbi",
    # generic
    "authority", "regulator", "regulatory", "enforcement",
]

# HARD "EVENT" patterns (keep these strong and specific)
EVENT_PATTERNS = [
    # sanctions / fines
    (r"\b(multa|sanzion|penalt|fine|ammenda)\b", "authority"),
    (r"\b(cease and desist|injunction|order)\b", "authority"),
    (r"\b(provvediment|delibera|deliberation|decisione|decision)\b", "authority"),
    (r"\b(ordinanza|ordinance)\b", "authority"),
    (r"\b(ispezion|inspection)\b", "authority"),

    # fraud / crime / investigations
    (r"\b(indagin|investigation|probe)\b", "judicial"),
    (r"\b(arrest|arrestat|custodia cautelare|detenut)\b", "judicial"),
    (r"\b(incriminat|indicted|charged)\b", "judicial"),
    (r"\b(condann|convict|sentenced)\b", "judicial"),
    (r"\b(truffa|frode|fraud|scam|riciclaggio|money laundering)\b", "judicial"),
    (r"\b(sequestro|seized|asset seizure)\b", "judicial"),

    # insolvency / bankruptcy (risk event)
    (r"\b(falliment|bankrupt|insolvenc|liquidation|receivership)\b", "judicial"),

    # class action
    (r"\b(class action|collective action|azione collettiva)\b", "class_action"),
]

# If none of these are present -> no signal
def _norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def classify_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: dict with keys {title, snippet, link, source, position}
    Output:
      - risk_level: "high" | "none"  (binary engine)
      - risk_type: "authority" | "judicial" | "class_action" | ""
      - authority: detected authority keyword if any
      - reason: short explanation
      - matched: list of matched tokens/patterns
    """
    title = result.get("title") or ""
    snippet = result.get("snippet") or ""
    link = result.get("link") or ""
    source = result.get("source") or ""

    blob = _norm(f"{title} {snippet} {source} {link}")

    matched: List[str] = []

    # detect authority keyword (optional)
    detected_authority: Optional[str] = None
    for k in AUTHORITY_KEYWORDS:
        if k and k in blob:
            detected_authority = k.upper()
            matched.append(k)
            break

    # detect HARD risk event patterns
    detected_type: Optional[str] = None
    for pattern, rtype in EVENT_PATTERNS:
        if re.search(pattern, blob, flags=re.IGNORECASE):
            detected_type = rtype
            matched.append(pattern)
            break

    # Binary decision:
    # - if we found a hard event pattern -> SIGNAL
    # - else -> NONE
    if not detected_type:
        return {
            "risk_level": "none",
            "risk_type": "",
            "authority": None,
            "reason": "",
            "matched": [],
        }

    # risk_level: HIGH for authority/judicial/class_action (binary)
    reason = "Risk event detected (binary engine)."
    if detected_type == "authority":
        reason = "Authority/regulator action detected."
    elif detected_type == "judicial":
        reason = "Judicial/enforcement event detected."
    elif detected_type == "class_action":
        reason = "Class action / collective redress detected."

    return {
        "risk_level": "high",
        "risk_type": detected_type,
        "authority": detected_authority,
        "reason": reason,
        "matched": matched[:6],
    }
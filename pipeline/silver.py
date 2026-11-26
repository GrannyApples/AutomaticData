import re
from pathlib import Path

import yaml
from rapidfuzz import fuzz, process

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "registry.yaml"
SUGGEST_THRESHOLD = 85

def load_schema() -> dict:
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))["fields"]


def _norm(name: str) -> str:
    """'Customer ID' och 'customer_id' blir båda 'customerid'."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


#this entire function is heavily coded with help from AI because I do not have enough expertise in fuzzy search
#or how to properly structure schema validation for flagging and sorting in a good way.
def map_columns(columns, schema = None, threshold= SUGGEST_THRESHOLD) -> dict:
    """Mappar källkolumner mot standardfälten. Okända kolumner flaggas, de tas aldrig bort."""
    schema = schema or load_schema()

    lookup = {}
    for canonical, spec in schema.items():
        for key in [canonical, *spec.get("synonyms", [])]:
            lookup[_norm(key)] = canonical

    mapped, remaining = {}, []
    for col in columns:
        target = lookup.get(_norm(col))
        if target is None or target in mapped.values():
            remaining.append(col)
        else:
            mapped[col] = target

    free = {k: v for k, v in lookup.items() if v not in mapped.values()}
    suggested, flagged = {}, []
    for col in remaining:
        best = process.extractOne(_norm(col), list(free), scorer=fuzz.WRatio) if free else None
        if best and best[1] >= threshold:
            suggested[col] = {"target": free[best[0]], "matched_on": best[0], "score": round(best[1], 1)}
        else:
            flagged.append(col)
    return {
        "mapped": mapped,
        "suggested": suggested,
        "flagged": flagged,
        "missing": [f for f in schema if f not in mapped.values()],
    }
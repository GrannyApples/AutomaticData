import re
from pathlib import Path

import yaml

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "registry.yaml"


def load_schema() -> dict:
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))["fields"]


def _norm(name: str) -> str:
    """'Customer ID' och 'customer_id' blir båda 'customerid'."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def map_columns(columns: list[str], schema: dict | None = None) -> dict:
    """Mappar källkolumner mot standardfälten. Okända kolumner flaggas, de tas aldrig bort."""
    schema = schema or load_schema()

    lookup = {}
    for canonical, spec in schema.items():
        for key in [canonical, *spec.get("synonyms", [])]:
            lookup[_norm(key)] = canonical

    mapped, flagged = {}, []
    for col in columns:
        target = lookup.get(_norm(col))
        if target is None or target in mapped.values():
            flagged.append(col)
        else:
            mapped[col] = target

    return {
        "mapped": mapped,
        "flagged": flagged,
        "missing": [f for f in schema if f not in mapped.values()],
    }
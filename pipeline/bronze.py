from sys import meta_path

import requests
import zipfile
import io
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BRONZE_DIR = Path(__file__).resolve().parent.parent / "data" / "bronze"

# initial test, sourced from test data i placed inside the exam doc
# sources in the future will most likely be taken from AI,
# so i dont have to scoure way to much documentation

SOURCES = {
    "online_retail_ii": {
        "url": "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip",
        "format": "zip",
        "inner_filename": "online_retail_II.xlsx",
    },
}


def fetch_from_api(url: str, timeout: int = 15) -> requests.Response:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def fetch_source(name: str, timeout: int = 15) -> requests.Response:
    if name not in SOURCES:
        raise ValueError(f"Okänd källa: '{name}'. Tillgängliga: {list(SOURCES)}")
    url = SOURCES[name]["url"]
    return fetch_from_api(url, timeout=timeout)

def extract_from_zip(zip_bytes: bytes, inner_filename: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        if inner_filename not in zf.namelist():
            raise ValueError(
                f"'{inner_filename}' finns inte i arkivet. Innehåll: {zf.namelist()}"
            )
        return zf.read(inner_filename)

def fetch_and_extract(name: str) -> bytes:
    """Hämtar en namngiven källa och packar ut filen ur zip-arkivet."""
    response = fetch_source(name)
    return extract_from_zip(response.content, SOURCES[name]["inner_filename"])

def save_bronze (name: str, raw_bytes: bytes)-> dict:
    """saves originalbytes in bronze layer plus metadata with SHA256"""
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    filenam= SOURCES[name]["inner_filename"]
    (BRONZE_DIR / filenam).write_bytes(raw_bytes)

    meta = {
        "source": name,
        "filename": filenam,
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "size_bytes": len(raw_bytes),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    (BRONZE_DIR / f"{name}.meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def get_raw(name: str) -> bytes:
    """reads from bronze if exists, otherwise fetch"""

    path = BRONZE_DIR / SOURCES[name]["inner_filename"]
    meta_path = BRONZE_DIR / f"{name}.meta.json"

    if path.exists() and meta_path.exists():
        raw = path.read_bytes()
        expected = json.loads(meta_path.read_text())["sha256"]
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"Hash not correct for {path.name}")
        return raw

    raw = fetch_and_extract(name)
    save_bronze(name, raw)
    return raw
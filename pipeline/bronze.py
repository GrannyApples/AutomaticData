import requests
import zipfile
import io

# initial test, sourced from test data i placed inside the exam doc
# sources in the future will most likely be taken from AI,
# so i dont have to scoure way to much documentation

SOURCES = {
    "online_retail_ii": {
        "url": "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip",
        "format": "zip",  # innehåller online_retail_II.xlsx — uppackning är nästa steg, inte det här
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
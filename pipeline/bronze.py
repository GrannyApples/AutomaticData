import requests

# initial test, sourced from test data i placed inside the exam doc
# sources will most likely be taken from AI so i dont have to scoure way to much documentation
SOURCES = {
    "online_retail_ii": {
        "url": "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip",
        "format": "zip",  # innehåller online_retail_II.xlsx — uppackning är nästa steg, inte det här
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
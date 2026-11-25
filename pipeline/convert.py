import io
import pandas as pd
import json
from pipeline.bronze import BRONZE_DIR, get_raw
def xlsx_to_dataframe(xlsx_bytes: bytes) -> dict[str, pd.DataFrame]:
    """Converts an xlsx file to a pandas dataframe"""
    return pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name=None)


## checked with AI it recommends using the ZSTD compression algorithm
# (Zstadnard is "just" a compression algo, won't be trying to understand it)
def dataframe_to_parquet_bytes(df: pd.DataFrame, compression: str = "zstd") -> bytes:
    """Converts a dataframe to a paraquet bytes"""
    buf = io.BytesIO()
    df.to_parquet(buf, engine="pyarrow", compression=compression, index=False)
    return buf.getvalue()


def find_mixed_type_columns(df: pd.DataFrame) -> dict[str, dict[str, int]]:
    """Hittar object kolumner som blandar Python-typer,
     tex single letter prefixes or suffixes
    like Invoice is usually just int64, but sometimes
    it has a C prefix(start letter) or A suffix(end letter)

    """
    result = {}
    for col in df.select_dtypes("object").columns:
        types = df[col].dropna().map(type).value_counts()
        if len(types) > 1:
            result[col] = {t.__name__: int(n) for t, n in types.items()}
    return result


def stringify_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Castar angivna kolumner till str. håller "nan" som null ."""
    out = df.copy()
    for col in columns:
        out[col] = out[col].where(out[col].isna(), out[col].astype(str))
    return out

def xlsx_bytes_to_parquet(xlsx_bytes: bytes) -> tuple[bytes, dict]:
    """XLSX to parquet bytes, with metadata"""
    sheets =xlsx_to_dataframe(xlsx_bytes)
    frames = list(sheets.values())

    columns = list(frames[0].columns)
    if any(list(f.columns) != columns for f in frames):
        raise ValueError("different columns cant merge")

    df = pd.concat(frames, ignore_index=True)
    mixed = find_mixed_type_columns(df)
    df = stringify_columns(df, list(mixed))
    parquet = dataframe_to_parquet_bytes(df, compression="gzip")

    metadata = {
        "sheets": list(sheets),
        "rows_in": sum(len(f) for f in frames),
        "rows_out": len(df),
        "columns": columns,
        "cast_to_str": list(mixed),
        "parquet_bytes": len(parquet),
    }
    return parquet, metadata

def get_parquet(name:str) -> bytes:
    """returns parquet bytes for given name else converts if cache is missing"""

    raw = get_raw(name)
    source_hash = json.loads((BRONZE_DIR / f"{name}.meta.json").read_text())["sha256"]
    parquet_path = BRONZE_DIR / f"{name}.parquet"
    json_path = BRONZE_DIR / f"{name}.convert.json"

    if parquet_path.exists() and json_path.exists():
        if json.loads(json_path.read_text()).get("source_sha256") == source_hash:
            return parquet_path.read_bytes()


    parquet, meta = xlsx_bytes_to_parquet(raw)
    meta["source_sha256"] = source_hash
    parquet_path.write_bytes(parquet)
    json_path.write_text(json.dumps(meta, indent=2))
    return parquet

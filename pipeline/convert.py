import io
import pandas as pd

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
import io
import pandas as pd

def xlsx_to_dataframe(xlsx_bytes: bytes) -> dict[str, pd.DataFrame]:
    """Converts an xlsx file to a pandas dataframe"""
    return pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name=None)
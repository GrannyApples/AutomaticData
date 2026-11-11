from faker import Faker
import io
import zipfile
from openpyxl import Workbook

def generate_customers(n: int, seed: int = 42) -> list[dict]:
    """Genererar n syntetiska kunder. Samma seed ger alltid samma data."""
    Faker.seed(seed)
    fake = Faker("sv_SE")
    return [
        {
            "customer_id": 10000 + i,
            "name": fake.name(),
            "email": fake.email(),
            "city": fake.city(),
        }
        for i in range(n)
    ]

#writes a list of xlsx-fil,
#these are used to fake data to make sure faker can create zip files and so on.

def to_xlsx_bytes(rows: list[dict]) -> bytes:
    wb = Workbook()
    ws =wb.active
    ws.append(list(rows[0].keys()))
    for row in rows:
        ws.append(list(row.values()))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

def pack_zip(inner_filename: str, content:bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(inner_filename, content)
    return buf.getvalue()


def build_delivery(rows: list[dict], inner_filename: str) -> bytes:
    return pack_zip(inner_filename, to_xlsx_bytes(rows))
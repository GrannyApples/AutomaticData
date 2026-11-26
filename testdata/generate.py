from faker import Faker
import io
import zipfile
from openpyxl import Workbook
import random
from datetime import datetime, timedelta

COUNTRIES = ["Sweden", "Norway", "Denmark", "Finland"]

# Källans kolumnnamn per standardfält. Det är facit: sanningen finns per konstruktion.
WEBSHOP_PROFILE = {
    "invoice_id": "Order No",
    "product_code": "sku_code",
    "product_name": "Prod. Name",
    "quantity": "qty",
    "order_timestamp": "Order Date",
    "unit_price": "price_each",
    "customer_id": "Kund-ID",
    "country": "Land",
}
# Kolumner som källan har men som inte finns i standardschemat
WEBSHOP_EXTRAS = ["Discount", "gift_wrap", "internal_note"]



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
def generate_orders(n, customers, products, seed=42):
    rng = random.Random(seed)
    #keep it constant to make it easier to test
    start = datetime(2024,1,1)
    rows = []
    for i in range(n):
        cust, prod = rng.choice(customers), rng.choice(products)
        rows.append(
            {
                "invoice_id": 700000+i,
                "product_code": prod["code"],
                "product_name": prod["name"],
                "quantity": rng.randint(1, 12),
                "order_timestamp": start + timedelta(minutes=rng.randint(0, 60*24*365)),
                "unit_price": prod["price"],
                "customer_id": cust["customer_id"],
                "country": rng.choice(COUNTRIES),
            })
    return rows

#okey this one is somewhat beyond me, I wanted to create a faker profile, so I have some additional things to test against
#asked AI to help after updating it about the project and some variables.

#altho I do understand what it is doing, I would probably not have been able to write it alone.
def make_source(rows, profile, extras, seed=42, null_rate=0.02, dup_rate =0.01, prefixed_id_every=50):
    rng = random.Random(seed)
    out = []
    for i, row in enumerate(rows):
        new = {profile[k]: v for k, v in row.items()}
        if prefixed_id_every and i % prefixed_id_every == 0:
            new[profile["invoice_id"]] = f"W{new[profile["invoice_id"]]}"
        for field in ("product_name", "customer_id"):
            if rng.random() < null_rate:
                new[profile[field]] = None
        new["Discount"] = rng.choice([0.0,0.0,0.0, 0.05, 0.1])
        new["gift_wrap"] = rng.random() < 0.1
        new["internal_note"] = rng.choice([None, None, None, "check stock", "vip"])
        out.append(new)

    n_dups = int(len(out)* dup_rate)
    out.extend(dict(rng.choice(out)) for _ in range(n_dups))

    columns = list(out[0].keys())
    rng.shuffle(columns)
    out = [{c: row[c] for c in columns} for row in out]
    truth = {src: field for field, src in profile.items()}
    truth.update({c: None for c in extras})
    return out, truth


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
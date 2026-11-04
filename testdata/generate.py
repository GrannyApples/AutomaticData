from faker import Faker


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
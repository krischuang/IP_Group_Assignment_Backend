from beanie import Document


class Counter(Document):
    name: str
    value: int = 0

    class Settings:
        name = "counters"

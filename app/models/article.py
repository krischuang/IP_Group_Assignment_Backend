from datetime import datetime
from beanie import Document


class Article(Document):
    article_id: int
    title: str
    content: str
    author_id: int
    summary: str | None = None
    create_time: datetime
    update_time: datetime

    class Settings:
        name = "articles"
from datetime import datetime
from beanie import Document


class Article(Document):
    article_id: int
    title: str
    summary: str | None = None
    content: str
    author_id: int
    create_time: datetime
    update_time: datetime

    class Settings:
        name = "articles"
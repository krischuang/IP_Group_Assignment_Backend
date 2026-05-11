from datetime import datetime
from beanie import Document


class Bookmark(Document):
    user_id: int
    article_id: int
    note: str | None = None
    created_at: datetime

    class Settings:
        name = "bookmarks"

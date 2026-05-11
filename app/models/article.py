from datetime import datetime
from typing import List, Optional
from beanie import Document


class Article(Document):
    article_id: int
    title: str
    content: str
    author_id: int
    summary: str | None = None
    ai_job_id: str | None = None
    ai_summary: str | None = None
    ai_key_points: Optional[List[str]] = None
    ai_tags: Optional[List[str]] = None
    create_time: datetime
    update_time: datetime

    class Settings:
        name = "articles"
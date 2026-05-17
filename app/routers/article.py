import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from app.models.article import Article
from app.dependencies import get_current_user
from app.models.user import User, UserRole
from app.utils.counter import _next_id
from app.routers.ai_tools import job_store, _run_summary_job

router = APIRouter(prefix="/articles", tags=["articles"])


# ---------- Schemas ----------

class ArticleCreate(BaseModel):
    title: str
    content: str


class ArticleUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class ArticleResponse(BaseModel):
    article_id: int
    title: str
    content: str
    author_id: int
    summary: str | None
    ai_job_id: str | None
    ai_summary: str | None
    ai_key_points: Optional[List[str]]
    ai_tags: Optional[List[str]]
    create_time: datetime
    update_time: datetime


# ---------- Helpers ----------


def _to_response(article: Article) -> ArticleResponse:
    return ArticleResponse(
        article_id=article.article_id,
        title=article.title,
        content=article.content,
        author_id=article.author_id,
        summary=article.summary,
        ai_job_id=article.ai_job_id,
        ai_summary=article.ai_summary,
        ai_key_points=article.ai_key_points,
        ai_tags=article.ai_tags,
        create_time=article.create_time,
        update_time=article.update_time,
    )


# ---------- Endpoints ----------

@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    body: ArticleCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    job_id = str(uuid.uuid4())

    article = Article(
        article_id=await _next_id("article_id"),
        title=body.title,
        content=body.content,
        author_id=current_user.user_id,
        ai_job_id=job_id,
        create_time=now,
        update_time=now,
    )

    await article.insert()

    job_store.create(job_id)
    background_tasks.add_task(_run_summary_job, job_id, body.content, article.article_id)

    return _to_response(article)


@router.get("/", response_model=list[ArticleResponse])
async def get_articles():
    articles = await Article.find_all().to_list()
    return [_to_response(a) for a in articles]


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int):
    article = await Article.find_one(Article.article_id == article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return _to_response(article)


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    body: ArticleUpdate,
    current_user: User = Depends(get_current_user),
):
    article = await Article.find_one(Article.article_id == article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if article.author_id != current_user.user_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    updates = body.model_dump(exclude_none=True)

    if updates:
        updates["update_time"] = datetime.now(timezone.utc)
        await article.update({"$set": updates})
        await article.sync()
    

    return _to_response(article)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(article_id: int, current_user: User = Depends(get_current_user)):
    article = await Article.find_one(Article.article_id == article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if article.author_id != current_user.user_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    await article.delete()
from datetime import datetime, timezone
from pymongo import ReturnDocument
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.models.article import Article
from app.models.counter import Counter
from app.dependencies import get_current_user
from app.models.user import User

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
    create_time: datetime
    update_time: datetime


# ---------- Helpers ----------

async def _next_article_id() -> int:
    collection = Counter.get_motor_collection()
    result = await collection.find_one_and_update(
        {"name": "article_id"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return result["value"]


def _to_response(article: Article) -> ArticleResponse:
    return ArticleResponse(
        article_id=article.article_id,
        title=article.title,
        content=article.content,
        author_id=article.author_id,
        create_time=article.create_time,
        update_time=article.update_time,
    )


# ---------- Endpoints ----------

@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(body: ArticleCreate, current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)

    article = Article(
        article_id=await _next_article_id(),
        title=body.title,
        summary=body.content[:120],
        content=body.content,
        author_id=current_user.user_id,
        create_time=now,
        update_time=now,
    )

    await article.insert()
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

    if article.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    updates = body.model_dump(exclude_none=True)

    if updates:
        updates["update_time"] = datetime.now(timezone.utc)
        if "content" in updates:
            updates["summary"] = updates["content"][:120]
        await article.update({"$set": updates})
        await article.sync()
    

    return _to_response(article)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(article_id: int, current_user: User = Depends(get_current_user)):
    article = await Article.find_one(Article.article_id == article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if article.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    await article.delete()
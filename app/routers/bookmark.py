from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.models.bookmark import Bookmark
from app.models.article import Article
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


# ---------- Schemas ----------

class BookmarkCreate(BaseModel):
    article_id: int
    note: str | None = None


class BookmarkUpdate(BaseModel):
    note: str | None = None


class BookmarkResponse(BaseModel):
    article_id: int
    note: str | None
    created_at: datetime
    article_title: str


# ---------- Endpoints ----------

@router.post("/", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(body: BookmarkCreate, current_user: User = Depends(get_current_user)):
    article = await Article.find_one(Article.article_id == body.article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    existing = await Bookmark.find_one(
        Bookmark.user_id == current_user.user_id,
        Bookmark.article_id == body.article_id,
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Article already bookmarked")

    bookmark = Bookmark(
        user_id=current_user.user_id,
        article_id=body.article_id,
        note=body.note,
        created_at=datetime.now(timezone.utc),
    )
    await bookmark.insert()
    return BookmarkResponse(
        article_id=bookmark.article_id,
        note=bookmark.note,
        created_at=bookmark.created_at,
        article_title=article.title,
    )


@router.get("/", response_model=list[BookmarkResponse])
async def list_bookmarks(current_user: User = Depends(get_current_user)):
    bookmarks = await Bookmark.find(Bookmark.user_id == current_user.user_id).to_list()
    result = []
    for b in bookmarks:
        article = await Article.find_one(Article.article_id == b.article_id)
        result.append(BookmarkResponse(
            article_id=b.article_id,
            note=b.note,
            created_at=b.created_at,
            article_title=article.title if article else f"Article #{b.article_id}",
        ))
    return result


@router.put("/{article_id}", response_model=BookmarkResponse)
async def update_bookmark(
    article_id: int,
    body: BookmarkUpdate,
    current_user: User = Depends(get_current_user),
):
    bookmark = await Bookmark.find_one(
        Bookmark.user_id == current_user.user_id,
        Bookmark.article_id == article_id,
    )
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")

    await bookmark.update({"$set": {"note": body.note}})
    await bookmark.sync()

    article = await Article.find_one(Article.article_id == article_id)
    return BookmarkResponse(
        article_id=bookmark.article_id,
        note=bookmark.note,
        created_at=bookmark.created_at,
        article_title=article.title if article else f"Article #{article_id}",
    )


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(article_id: int, current_user: User = Depends(get_current_user)):
    bookmark = await Bookmark.find_one(
        Bookmark.user_id == current_user.user_id,
        Bookmark.article_id == article_id,
    )
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    await bookmark.delete()

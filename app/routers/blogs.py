from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user
from ..database import get_db
from ..models import Blog, User
from ..schemas import BlogCreate, BlogOut

router = APIRouter(prefix="/api/blogs", tags=["blogs"])


def serialize_blog(blog: Blog) -> dict:
    return {
        "id": blog.id,
        "title": blog.title,
        "content": blog.content,
        "author_id": blog.author_id,
        "author_username": blog.author.username,
        "created_at": blog.created_at,
    }


@router.get("", response_model=list[BlogOut])
def list_blogs(db: Session = Depends(get_db)):
    blogs = (
        db.query(Blog)
        .options(joinedload(Blog.author))
        .order_by(Blog.created_at.desc())
        .all()
    )
    return [serialize_blog(b) for b in blogs]


@router.get("/{blog_id}", response_model=BlogOut)
def get_blog(blog_id: int, db: Session = Depends(get_db)):
    blog = (
        db.query(Blog)
        .options(joinedload(Blog.author))
        .filter(Blog.id == blog_id)
        .first()
    )
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return serialize_blog(blog)


@router.post("", response_model=BlogOut, status_code=status.HTTP_201_CREATED)
def create_blog(
    payload: BlogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    blog = Blog(
        title=payload.title,
        content=payload.content,
        author_id=current_user.id,
    )
    db.add(blog)
    db.commit()
    db.refresh(blog)
    blog = (
        db.query(Blog)
        .options(joinedload(Blog.author))
        .filter(Blog.id == blog.id)
        .first()
    )
    return serialize_blog(blog)

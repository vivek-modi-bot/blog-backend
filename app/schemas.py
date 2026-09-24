from datetime import datetime

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    bio: str | None = None
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class PublicUserOut(BaseModel):
    id: int
    username: str
    bio: str | None = None
    avatar_url: str | None = None
    blog_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    bio: str | None = Field(default=None, max_length=500)


class BlogCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class BlogUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class BlogOut(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    author_username: str
    author_avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    like_count: int = 0
    comment_count: int = 0
    liked_by_me: bool = False

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: int
    content: str
    user_id: int
    username: str
    avatar_url: str | None = None
    blog_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class LikeOut(BaseModel):
    liked: bool
    like_count: int

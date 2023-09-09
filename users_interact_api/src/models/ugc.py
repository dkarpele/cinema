from datetime import datetime
from uuid import UUID

from pydantic import Field

from models.model import Model


class View(Model):
    movie_id: UUID
    begin_time: datetime
    end_time: datetime


class RequestModel(Model):
    movie_id: UUID


class LikesModel(Model):
    user_id: UUID
    movie_id: UUID
    rating: int


class LikesCountMovieModel(Model):
    movie_id: UUID
    likes_count: int
    dislikes_count: int


class MovieAvgModel(Model):
    movie_id: UUID
    avg_rating: float


class RequestReviewModel(RequestModel):
    review: str


class RequestReviewIdModel(Model):
    review_id: str


class ReviewResponseModel(Model):
    user_id: UUID
    movie_id: UUID
    movie_title: str
    review: str
    date: datetime = Field(default_factory=datetime.utcnow)
    likes_amount: int = 0
    dislikes_amount: int = 0


class LikedReviewModel(Model):
    review_id: str
    user_id: UUID
    rating: int
    # Like added time
    date: datetime = Field(default_factory=datetime.utcnow)


class BookmarksResponseModel(Model):
    user_id: UUID
    movie_id: UUID

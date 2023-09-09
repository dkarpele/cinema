from typing import List, Annotated, Dict

from fastapi import APIRouter, status, Depends, Query

from core import config as conf
from models.model import PaginateModel
from models.ugc import RequestReviewModel, ReviewResponseModel, RequestModel, \
    LikedReviewModel, RequestReviewIdModel
from services.likes import add_like_to_review_helper, users_daily_likes_helper
from services.mongo import MongoDep, get_data, insert_data
from services.token import security_jwt
from services.helpers import get_api_helper

# Объект router, в котором регистрируем обработчики
router = APIRouter()

Paginate = Annotated[PaginateModel, Depends(PaginateModel)]


@router.post('/add-review',
             response_model=ReviewResponseModel,
             status_code=status.HTTP_201_CREATED,
             description="создание рецензии на фильм",
             response_description="user_id, movie_id, review, date, "
                                  "likes to review")
async def add_review(token: Annotated[str, Depends(security_jwt)],
                     review: RequestReviewModel,
                     mongo: MongoDep) -> ReviewResponseModel:
    collection = 'reviews'

    # Getting user id from token
    url = f'http://{conf.settings.host_auth}:' \
          f'{conf.settings.port_auth}' \
          f'/api/v1/users/me'
    header = {'Authorization': f'Bearer {token}'}
    user_id = await get_api_helper(url, header)

    # Getting move title from movie id
    url = f'http://{conf.settings.host_content}:' \
          f'{conf.settings.port_content}' \
          f'/api/v1/films/{review.movie_id}'
    movie_title = await get_api_helper(url)

    review_document = {'user_id': user_id['id'],
                       'movie_id': review.movie_id,
                       'movie_title': movie_title['title'],
                       'review': review.review}
    res = ReviewResponseModel(**review_document)
    await insert_data(mongo, res, collection)
    return res


@router.get('/list-reviews',
            response_model=List,
            status_code=status.HTTP_200_OK,
            description="получение списка рецензий к фильму",
            response_description="list of user_id, movie_id, review, date, "
                                 "likes to review")
async def list_reviews(movie: Annotated[RequestModel,
                                        Depends(RequestModel)],
                       mongo: MongoDep,
                       pagination: Paginate,
                       sort: str = Query(None,
                                         description='Sort by date or likes'
                                                     ' amount. Use - before '
                                                     'sorting method to be asc'
                                                     ' or desc relatively'),
                       ) -> List:

    try:
        if sort.startswith('-'):
            sort_ = (sort[1:], -1)
        else:
            sort_ = (sort, 1)
    except AttributeError:
        sort_ = None
    collection = 'reviews'
    reviews_query = {'movie_id': str(movie.movie_id)}

    res = await get_data(mongo,
                         reviews_query,
                         collection,
                         {'movie_id': 0},
                         sort=sort_,
                         page=pagination.page_number,
                         size=pagination.page_size)
    return res


@router.post('/add-like-to-review',
             response_model=LikedReviewModel,
             status_code=status.HTTP_201_CREATED,
             description="поставить лайк на рецензию",
             response_description="review_id, user_id, rating")
async def add_like_to_review(token: Annotated[str, Depends(security_jwt)],
                             review: RequestReviewIdModel,
                             mongo: MongoDep) -> LikedReviewModel:
    res = await add_like_to_review_helper(review, mongo, token, 10)
    return res


@router.post('/add-dislike-to-review',
             response_model=LikedReviewModel,
             status_code=status.HTTP_201_CREATED,
             description="поставить disлайк на рецензию",
             response_description="review_id, user_id, rating")
async def add_dislike_to_review(
        token: Annotated[str, Depends(security_jwt)],
        review: RequestReviewIdModel,
        mongo: MongoDep) -> LikedReviewModel:
    res = await add_like_to_review_helper(review, mongo, token, 0)
    return res


@router.get('/users-daily-likes',
            # include_in_schema=False,
            response_model=Dict,
            status_code=status.HTTP_200_OK,
            description="get likes count for users for time period",
            response_description="""
            {
                "user_id": [
                    [
                        "movie_id",
                        "movie_title",
                        "review_text shortened to 20 signs",
                        likes amount for the last 24 hours (int)
                    ]
                ]
            }""")
async def users_daily_likes(mongo: MongoDep,) -> Dict:
    res = await users_daily_likes_helper(mongo)
    return res

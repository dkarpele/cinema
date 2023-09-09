from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Depends

from core import config as conf
from models.ugc import RequestModel, LikesModel, MovieAvgModel, \
    LikesCountMovieModel
from services.likes import set_like_to_movie_helper
from services.mongo import MongoDep, delete_data, get_aggregated, \
    get_count, get_data
from services.token import security_jwt
from services.helpers import get_api_helper

# Объект router, в котором регистрируем обработчики
router = APIRouter()
collection = 'likes'


@router.post('/like',
             response_model=LikesModel,
             status_code=status.HTTP_201_CREATED,
             description="создание like на фильм",
             response_description="user_id, film_id, rating")
async def set_like(token: Annotated[str, Depends(security_jwt)],
                   like: RequestModel,
                   mongo: MongoDep) -> LikesModel:
    res = await set_like_to_movie_helper(like, mongo, token, 10)
    return res


@router.post('/dislike',
             response_model=LikesModel,
             status_code=status.HTTP_201_CREATED,
             description="создание dislike на фильм",
             response_description="user_id, film_id, rating")
async def set_dislike(token: Annotated[str, Depends(security_jwt)],
                      dislike: RequestModel,
                      mongo: MongoDep) -> LikesModel:
    res = await set_like_to_movie_helper(dislike, mongo, token, 0)
    return res


@router.get('/avg-movie-rating',
            response_model=MovieAvgModel,
            status_code=status.HTTP_200_OK,
            description="просмотр средней пользовательской оценки фильма",
            response_description="movie_id, rating")
async def average_movie_rating(movie: Annotated[RequestModel,
                                                Depends(RequestModel)],
                               mongo: MongoDep) -> MovieAvgModel:
    avg_query = [
        {
            '$match': {
                'movie_id': str(movie.movie_id)
            }
        },
        {
            '$group': {
                '_id': "$movie_id",
                'avg_rating': {
                    '$avg': "$rating"
                }
            }
        }
    ]
    res = await get_aggregated(mongo, avg_query, collection)
    if len(res) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie not found!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    first_res = res[0]
    first_res['movie_id'] = first_res.pop('_id')
    first_res['avg_rating'] = round(first_res['avg_rating'], 1)
    return MovieAvgModel(**first_res)


@router.get('/likes-dislikes-count-movie',
            response_model=LikesCountMovieModel,
            status_code=status.HTTP_200_OK,
            description="просмотр количества лайков и дизлайков у фильма",
            response_description="movie_id, likes_count, dislikes_count")
async def likes_count_movie(movie: Annotated[RequestModel,
                                             Depends(RequestModel)],
                            mongo: MongoDep) -> LikesCountMovieModel:

    films = await get_data(mongo,
                           {"movie_id": str(movie.movie_id)},
                           collection)
    if len(films) == 0:
        res = {"movie_id": movie.movie_id,
               'likes_count': 0,
               'dislikes_count': 0}
        return LikesCountMovieModel(**res)

    likes_count_query = {"movie_id": str(movie.movie_id),
                         "rating": 10}
    likes_count = await get_count(mongo,
                                  likes_count_query,
                                  collection)
    dislikes_count_query = {"movie_id": str(movie.movie_id),
                            "rating": 0}
    dislikes_count = await get_count(mongo,
                                     dislikes_count_query,
                                     collection)
    res = {"movie_id": movie.movie_id,
           'likes_count': likes_count,
           'dislikes_count': dislikes_count}
    return LikesCountMovieModel(**res)


@router.delete('/like',
               status_code=status.HTTP_204_NO_CONTENT,
               description="удаление like or dislike у юзера", )
async def delete_like(token: Annotated[str, Depends(security_jwt)],
                      like: RequestModel,
                      mongo: MongoDep):
    url = f'http://{conf.settings.host_auth}:'\
          f'{conf.settings.port_auth}'\
          f'/api/v1/users/me'
    header = {'Authorization': f'Bearer {token}'}
    user_id = await get_api_helper(url, header)

    like_document = {'user_id': user_id['id'], 'movie_id': like.movie_id}
    res = await delete_data(mongo,
                            like_document,
                            collection)
    if res.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Like not found!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

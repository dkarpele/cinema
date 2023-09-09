from bson import ObjectId
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from core import config as conf
from models.ugc import RequestReviewIdModel, LikedReviewModel, RequestModel, \
    LikesModel
from services.mongo import MongoDep, update_data, get_count, get_aggregated, \
    get_data
from services.helpers import get_api_helper


async def add_like_to_review_helper(review: RequestReviewIdModel,
                                    mongo: MongoDep,
                                    token: str | None = None,
                                    rating: int = 10) -> LikedReviewModel:
    # check if review_id really exists
    review_exists = await get_count(
        mongo,
        {'_id': ObjectId(review.review_id)},
        'reviews')
    if review_exists == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f'{review.review_id} review does not exist',
                            headers={"WWW-Authenticate": "Bearer"}, )

    collection = 'review_likes'
    url = f'http://{conf.settings.host_auth}:' \
          f'{conf.settings.port_auth}' \
          f'/api/v1/users/me'
    header = {'Authorization': f'Bearer {token}'}
    user_id = await get_api_helper(url, header)
    user_id = user_id['id']

    # add info about review_id, user_id, his like/dislike to review_likes
    query = {'user_id': user_id,
             'review_id': ObjectId(review.review_id)}
    review_document = {'user_id': user_id,
                       'review_id': ObjectId(review.review_id),
                       'rating': rating,
                       'date': datetime.utcnow()}
    await update_data(mongo, query, review_document, collection)

    # get likes_amount/dislikes_amount from review_likes

    liked_review_amount = await get_count(
        mongo,
        {'review_id': ObjectId(review.review_id),
         'rating': 10},
        collection)
    disliked_review_amount = await get_count(
        mongo,
        {'review_id': ObjectId(review.review_id),
         'rating': 0},
        collection)

    # add data about likes_amount/dislikes_amount to reviews by review_id(_id)
    likes_amount_doc = {'likes_amount': liked_review_amount,
                        'dislikes_amount': disliked_review_amount}
    await update_data(mongo,
                      {'_id': ObjectId(review.review_id)},
                      likes_amount_doc,
                      'reviews')

    review_document['review_id'] = str(review_document.get('review_id'))
    res = LikedReviewModel(**review_document)
    return res


async def set_like_to_movie_helper(like: RequestModel,
                                   mongo: MongoDep,
                                   token: str | None = None,
                                   rating: int = 10) -> LikesModel:
    collection = 'likes'
    url = f'http://{conf.settings.host_auth}:' \
          f'{conf.settings.port_auth}' \
          f'/api/v1/users/me'
    header = {'Authorization': f'Bearer {token}'}
    user_id = await get_api_helper(url, header)
    user_id = user_id['id']

    like_document = {'user_id': user_id,
                     'movie_id': str(like.movie_id),
                     'rating': rating}
    res = LikesModel(**like_document)
    await update_data(mongo,
                      {'user_id': user_id,
                       'movie_id': str(like.movie_id)},
                      like_document,
                      collection)
    return res


async def users_daily_likes_helper(mongo: MongoDep):
    query: list = [
        {
            '$match': {
                'rating': 10,
                'date': {
                    '$gt': datetime.utcnow() - timedelta(days=1)
                }
            }
        },
        {
            '$group': {
                '_id': '$review_id',
                'likes_amount_24_hours': {
                    '$count': {}
                }
            }
        }
    ]
    likes_amount = await get_aggregated(mongo, query, 'review_likes')

    query1: dict = {
        '_id': {
            '$in': [ObjectId(i['_id']) for i in likes_amount]
        }
    }
    reviews = await get_data(mongo, query1, 'reviews')
    user_daily_likes: dict = {}
    for like in likes_amount:
        for review in reviews:
            if like['_id'] == review['_id']:
                tuple_to_append = (review['movie_id'],
                                   review['movie_title'],
                                   review['review'][:20],
                                   like['likes_amount_24_hours'])
                if review['user_id'] in user_daily_likes.keys():
                    user_daily_likes[review['user_id']].append(tuple_to_append)
                else:
                    user_daily_likes.update(
                        {review['user_id']: [tuple_to_append]})
                reviews.remove(review)
                break
    return user_daily_likes

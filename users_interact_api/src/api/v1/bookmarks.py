from typing import List, Annotated

from fastapi import APIRouter, status, HTTPException, Depends

from core import config as conf
from models.ugc import RequestModel, BookmarksResponseModel
from services.mongo import MongoDep, update_data, get_data, delete_data
from services.token import security_jwt
from services.helpers import get_api_helper

# Объект router, в котором регистрируем обработчики
router = APIRouter()
collection = 'bookmarks'


@router.post('/bookmarks',
             response_model=BookmarksResponseModel,
             status_code=status.HTTP_201_CREATED,
             description="создание закладки на фильм",
             response_description="user_id, film_id")
async def set_document_bookmarks(token: Annotated[str, Depends(security_jwt)],
                                 bookmark: RequestModel,
                                 mongo: MongoDep) -> BookmarksResponseModel:
    url = f'http://{conf.settings.host_auth}:'\
          f'{conf.settings.port_auth}'\
          f'/api/v1/users/me'
    header = {'Authorization': f'Bearer {token}'}
    user_id = await get_api_helper(url, header)

    bookmark_document = {'user_id': user_id['id'],
                         'movie_id': str(bookmark.movie_id)}
    res = BookmarksResponseModel(**bookmark_document)
    await update_data(mongo,
                      bookmark_document,
                      bookmark_document,
                      collection)
    return res


@router.get('/bookmarks',
            response_model=List,
            status_code=status.HTTP_200_OK,
            description="получение списка закладок пользователя",
            response_description="movie_id")
async def get_document_bookmarks(token: Annotated[str, Depends(security_jwt)],
                                 mongo: MongoDep) -> List:
    url = f'http://{conf.settings.host_auth}:' \
          f'{conf.settings.port_auth}' \
          f'/api/v1/users/me'
    header = {'Authorization': f'Bearer {token}'}
    user_id = await get_api_helper(url, header)

    bookmark_query = {'user_id': str(user_id['id'])}

    res = await get_data(mongo,
                         bookmark_query,
                         collection,
                         {'movie_id': 1, '_id': 0}
                         )
    return res


@router.delete('/bookmarks',
               status_code=status.HTTP_204_NO_CONTENT,
               description="удаление закладки у юзера",)
async def delete_document_bookmarks(
                            token: Annotated[str, Depends(security_jwt)],
                            bookmark: RequestModel,
                            mongo: MongoDep):
    url = f'http://{conf.settings.host_auth}:'\
          f'{conf.settings.port_auth}'\
          f'/api/v1/users/me'
    header = {'Authorization': f'Bearer {token}'}
    user_id = await get_api_helper(url, header)

    bookmark_document = {'user_id': user_id['id'],
                         'movie_id': bookmark.movie_id}
    res = await delete_data(mongo,
                            BookmarksResponseModel(**bookmark_document),
                            collection)
    if res.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bookmark not found!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

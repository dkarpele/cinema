from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder

from core import config as conf
from models.ugc import View
from services.database import KafkaDep
from services.token import security_jwt
from services.helpers import get_api_helper

# Объект router, в котором регистрируем обработчики
router = APIRouter()


@router.post('/send-movie-time',
             response_model=dict,
             status_code=HTTPStatus.CREATED,
             description="создание записи о просмотре",
             response_description="movie_id, begin_time, end_time")
async def create_view(token: Annotated[str, Depends(security_jwt)],
                      view: View,
                      kafka: KafkaDep) -> dict:
    url = f'http://{conf.settings.host_auth}:' \
          f'{conf.settings.port_auth}' \
          f'/api/v1/users/me'
    header = {'Authorization': f'Bearer {token}'}
    user_id = await get_api_helper(url, header)
    user_id = user_id['id']
    await kafka.produce_viewed_frame(user_id,
                                     view.movie_id,
                                     view.begin_time,
                                     view.end_time)
    view_dto = jsonable_encoder(view)
    view_dto['user_id'] = user_id
    return view_dto

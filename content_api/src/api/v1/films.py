from uuid import UUID

import core.config as conf

from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Query, status as st
from typing import Annotated

from api.v1 import _details, _list, _get_cache_key
from services.service import IdRequestService, ListService
from services.film import get_film_service, get_film_list_service

from services.token import security_jwt, check_roles
from models.model import Model, PaginateModel

# FastAPI в качестве моделей использует библиотеку pydantic
# https://pydantic-docs.helpmanual.io
# У неё есть встроенные механизмы валидации, сериализации и десериализации
# Также она основана на дата-классах

# Объект router, в котором регистрируем обработчики
router = APIRouter()
Paginate = Annotated[PaginateModel, Depends(PaginateModel)]
INDEX = 'movies'


class FilmList(Model):
    uuid: str
    title: str
    imdb_rating: float | None = None


class Film(FilmList):
    description: str | None = None
    genre: list[dict] | None = None
    actors: list[dict] | None = None
    writers: list[dict] | None = None
    directors: list[dict] | None = None


@router.get('/search',
            response_model=list[FilmList],
            summary="Поиск кинопроизведений",
            description="Полнотекстовый поиск по кинопроизведениям",
            response_description="Название и рейтинг фильма",
            tags=['Полнотекстовый поиск']
            )
async def film_search(pagination: Paginate,
                      film_service: ListService = Depends(
                          get_film_list_service),
                      query: str = Query(None,
                                         description=conf.SEARCH_DESC),
                      sort: str = Query(None,
                                        description=conf.SORT_DESC),
                      ) -> list[FilmList]:
    page = pagination.page_number
    size = pagination.page_size
    if query:
        search = {
            "bool": {
                "must":
                    {"match": {"title": query}}
            }
        }
    else:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f'Empty `query` attribute')

    # Redis caching
    key = await _get_cache_key({'sort': sort,
                                'query': query,
                                'page': page,
                                'size': size},
                               INDEX)

    films = await _list(film_service,
                        index=INDEX,
                        search=search,
                        sort=sort,
                        key=key,
                        page=page,
                        size=size)

    res = [FilmList(uuid=film.id,
                    title=film.title,
                    imdb_rating=film.imdb_rating) for film in films]
    return res


@router.post('/films-titles',
             response_model=list[tuple],
             summary="Названия фильмов по id",
             response_description="названия фильмов",
             )
async def films_details(
        film_ids_list: list[UUID],
        film_service: ListService = Depends(get_film_list_service)) \
        -> list[tuple]:
    if film_ids_list:
        search = {
            "ids": {
                "values": film_ids_list
            }
        }
    else:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f'Empty `film_ids_list` attribute')

    films = await _list(film_service,
                        index=INDEX,
                        search=search,
                        )

    res = [(film.id, film.title) for film in films]
    return res


# С помощью декоратора регистрируем обработчик film_details
# На обработку запросов по адресу <some_prefix>/some_id
# Позже подключим роутер к корневому роутеру
# И адрес запроса будет выглядеть так — /api/v1/films/some_id
# В сигнатуре функции указываем тип данных, получаемый из адреса запроса
# (film_id: str)
# И указываем тип возвращаемого объекта — Film
# Внедряем IdRequestService с помощью Depends(get_film_service)
@router.get('/{film_id}',
            response_model=Film,
            summary="Детали фильма",
            description="Доступная информация по одному фильму",
            response_description="id, название, рейтинг, описание, жанр, "
                                 "список актеров, режиссеров и сценаристов",
            )
async def film_details(
        # token: Annotated[str, Depends(security_jwt)],
        film_service: IdRequestService = Depends(get_film_service),
        film_id: str = None,
) -> Film:
    # await check_roles(token, 'manager admin')
    film = await _details(film_service, film_id, INDEX)

    # Перекладываем данные из models.Film в Film.
    # Обратите внимание, что у модели бизнес-логики есть поле description,
    # которое отсутствует в модели ответа API.
    # Если бы использовалась общая модель для бизнес-логики и формирования
    # ответов API вы бы предоставляли клиентам данные, которые им не нужны
    # и, возможно, данные, которые опасно возвращать

    return Film(uuid=film.id,
                title=film.title,
                imdb_rating=film.imdb_rating,
                description=film.description,
                genre=film.genre,
                actors=film.actors,
                writers=film.writers,
                directors=film.directors)


@router.get('/',
            response_model=list[FilmList],
            summary="Список фильмов",
            description="Список фильмов с информацией о id, названии, рейтинге",
            response_description="id, название, рейтинг",
            )
async def film_list(pagination: Paginate,
                    film_service: ListService = Depends(get_film_list_service),
                    sort: str = Query(None,
                                      description=conf.SORT_DESC),
                    genre: str = Query(None,
                                       description=conf.GENRE_DESC)
                    ) -> list[FilmList]:
    page = pagination.page_number
    size = pagination.page_size

    if genre:
        search = {
            "nested": {
                "path": "genre",
                "query": {
                    "bool": {
                        "must":
                            {"match": {"genre.name": genre}}
                    }
                }
            }
        }
    else:
        search = None

    key = await _get_cache_key({'sort': sort,
                                'genre': genre,
                                'page': page,
                                'size': size},
                               INDEX)

    films = await _list(film_service,
                        index=INDEX,
                        sort=sort,
                        search=search,
                        key=key,
                        page=page,
                        size=size)

    res = [FilmList(uuid=film.id,
                    title=film.title,
                    imdb_rating=film.imdb_rating) for film in films]
    return res

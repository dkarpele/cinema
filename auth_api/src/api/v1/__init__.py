from fastapi import HTTPException, status
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from services.exceptions import entity_doesnt_exist


async def _get_cache_key(args_dict: dict = None,
                         index: str = None) -> str:
    if not args_dict:
        args_dict = {}

    key = ''
    for k, v in args_dict.items():
        if v:
            key += f':{k}:{v}'

    return f'index:{index}{key}' if key else f'index:{index}'


async def check_entity_exists(db: AsyncSession,
                              table,
                              search_value):
    try:
        exists = await db.get(table, search_value)
    except DBAPIError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'{search_value} not found for '
                                   f'{str(table)}',
                            headers={"WWW-Authenticate": "Bearer"})
    if not exists:
        raise entity_doesnt_exist(table.__name__, str(search_value))
    return exists

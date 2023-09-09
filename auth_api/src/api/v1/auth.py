from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from schemas.users import UserSignUp, UserResponseData, UserLogin
from services.database import DbDep, CacheDep
from services.token import Token, add_not_valid_access_token_to_cache, \
    refresh_access_token, TokenDep
from services.users import register_user, \
    login_for_access_token, login_for_user_data, get_all_roles_for_user

# Объект router, в котором регистрируем обработчики
router = APIRouter()


@router.post('/signup',
             response_model=UserResponseData,
             status_code=HTTPStatus.CREATED,
             description="регистрация нового пользователя",
             response_description="id, email, hashed password")
async def create_user(user_create: UserSignUp, db: DbDep) -> UserResponseData:
    user = await register_user(user_create, db)
    user.roles = await get_all_roles_for_user(token=None,
                                              user_id=str(user.id),
                                              db=db)
    return user


@router.post("/login",
             response_model=Token,
             status_code=HTTPStatus.OK,
             description="login существующего пользователя",
             response_description="Возвращает токены"
             )
async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: DbDep,
        cache: CacheDep) -> Token:
    tokens = await login_for_access_token(form_data, db, cache)
    return tokens


@router.post("/login-sso",
             response_model=UserResponseData,
             status_code=HTTPStatus.OK,
             description="login существующего пользователя",
             response_description="Возвращает модель User"
             )
async def login_sso(
        form_data: UserLogin | dict,
        db: DbDep) -> UserResponseData:
    user = await login_for_user_data(form_data, db)
    user.roles = await get_all_roles_for_user(token=None,
                                              user_id=str(user.id),
                                              db=db)

    return user


@router.post("/logout",
             description="выход пользователя из аккаунта",
             status_code=HTTPStatus.OK)
async def logout(
        token: TokenDep, cache: CacheDep) -> None:
    await add_not_valid_access_token_to_cache(token, cache)


@router.post("/refresh",
             response_model=Token,
             description="получить новую пару access/refresh token",
             status_code=HTTPStatus.OK)
async def refresh(token: str, cache: CacheDep) -> Token:
    res = await refresh_access_token(token, cache)
    return res

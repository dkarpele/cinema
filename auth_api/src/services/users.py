import logging
from typing import Annotated, Union
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import and_
from sqlalchemy.future import select

from api.v1 import check_entity_exists
from models.history import LoginHistory
from models.roles import UserRole, Role
from models.users import User, SocialAccount
from schemas.roles import RoleCreate
from schemas.users import UserInDB, UserSignUp, UserSignUpOAuth, \
    UserResponseData, UserLogin
from services.database import DbDep, CacheDep
from services.exceptions import credentials_exception, \
    wrong_username_or_password
from services.token import verify_password, TokenData, \
    SECRET_KEY, decode_token, oauth2_scheme, Token, create_token, \
    check_access_token


async def get_user(db: DbDep,
                   _id: str = None,
                   email: str = None):
    async with db:
        if _id:
            user_exists = await db.execute(
                select(User).
                where(User.id == _id))
        elif email:
            user_exists = await db.execute(
                select(User).
                where(User.email == email))
        else:
            raise logging.exception("Parameters _id or email weren't "
                                    "fulfilled")
        user = user_exists.scalars().all()
        if user:
            user_roles = await get_all_roles_for_user(token=None,
                                                      user_id=str(user[0].id),
                                                      db=db)
            user_dto = jsonable_encoder(user[0])
            user_dto['roles'] = user_roles
            return UserInDB(**user_dto)


async def authenticate_user(username: str,
                            password: str,
                            db: DbDep):
    user = await get_user(email=username, db=db)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           db: DbDep):
    _id, _ = await decode_token(token, SECRET_KEY)
    token_data = TokenData(id=_id)
    user = await get_user(_id=token_data.id, db=db)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Inactive user",
                            headers={"WWW-Authenticate": "Bearer"})
    return current_user


async def check_admin_user(token: Annotated[str, Depends(oauth2_scheme)],
                           db: DbDep):
    try:
        user_id, _ = await decode_token(token, SECRET_KEY)

        roles_exists = await db.execute(
            select(UserRole).
            filter(UserRole.user_id == user_id)
        )
        all_roles = [row.role_id for row in roles_exists.scalars().all()]
        permissions = 0
        for r_id in all_roles:
            response = await db.execute(select(Role).filter(Role.id == r_id))
            role = response.scalars().first()
            if role.permissions > permissions:
                permissions = role.permissions
        admin = await db.execute(
            select(Role).
            filter(Role.title == 'admin')
        )
        if admin.scalars().first().permissions <= permissions:
            return True
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have permission to access on "
                                   "this server.",
                            headers={"WWW-Authenticate": "Bearer"})
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Role admin not found.",
                            headers={"WWW-Authenticate": "Bearer"})


async def register_user(user_create: Union[UserSignUp, UserSignUpOAuth],
                        db: DbDep) -> User:
    user_dto = jsonable_encoder(user_create)
    user = User(**user_dto)

    async with db:
        user_exists = await db.execute(
            select(User).
            filter(User.email == user.email))

        if user_exists.scalars().all():
            if type(user_create) == UserSignUp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Email {user.email} already exists",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return user
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def register_oauth_user(user_create: UserSignUpOAuth,
                              db: DbDep) -> User:

    async with db:
        oauth_user_exists = await db.execute(
            select(SocialAccount).
            filter(and_(SocialAccount.social_id == user_create.social_id,
                        SocialAccount.social_name == user_create.social_name)))

        user_dto = jsonable_encoder(user_create)
        if not oauth_user_exists.scalars().all():

            user = await register_user(UserSignUp(**user_dto), db)
            oauth_user = SocialAccount(social_id=user_create.social_id,
                                       social_name=user_create.social_name,
                                       user_id=user.id)
            db.add(oauth_user)
            await db.commit()
            await db.refresh(oauth_user)
            return user
        else:
            logging.info(f'{user_create.social_name} user {user_create.email} '
                         f'already exists')
            user_dto.pop('social_id')
            user_dto.pop('social_name')
            return User(**user_dto)


async def login_for_access_token(
        form_data: Union[OAuth2PasswordRequestForm, User],
        db: DbDep,
        cache: CacheDep) -> Token:
    if isinstance(form_data, OAuth2PasswordRequestForm):
        user = await authenticate_user(form_data.username,
                                       form_data.password,
                                       db)
    else:
        user = await get_user(db=db, email=form_data.email)
    if not user:
        raise wrong_username_or_password

    await add_history(db=db, user_id=user.id)

    token_structure = await create_token({"sub": str(user.id)}, cache)
    return Token(**token_structure)


async def login_for_user_data(
        form_data: UserLogin,
        db: DbDep) -> UserResponseData | None:
    if isinstance(form_data, dict):
        username = form_data['username']
        password = form_data['password']
    else:
        username = form_data.email
        password = form_data.password

    user = await authenticate_user(username, password, db)
    if not user:
        raise wrong_username_or_password

    await add_history(db=db, user_id=user.id)

    user.roles = await get_all_roles_for_user(token=None,
                                              user_id=str(user.id),
                                              db=db)
    return UserResponseData(**jsonable_encoder(user))


async def add_history(db: DbDep,
                      user_id: UUID,
                      source: str = None) -> None:
    history = LoginHistory(user_id, source)
    db.add(history)
    await db.commit()
    await db.refresh(history)


async def get_all_roles_for_user(
        db: DbDep,
        token: Annotated[str | None, Depends(oauth2_scheme)],
        user_id: str = None,
        return_permissions: bool = False) -> set[RoleCreate]:

    if not user_id and token:
        user_id, _ = await decode_token(token, SECRET_KEY)

    async with db:
        await check_entity_exists(db, User, user_id)

        roles_exists = await db.execute(
            select(UserRole).
            filter(UserRole.user_id == user_id)
        )
        all_roles = [row.role_id for row in roles_exists.scalars().all()]
        roles = []
        for r_id in all_roles:
            response = await db.execute(
                select(Role).
                filter(Role.id == r_id)
            )
            role = response.scalars().first()
            roles.append(RoleCreate(title=role.title,
                                    permissions=role.permissions))

        user_roles_set = {role.title.lower() for role in roles}
        return user_roles_set if not return_permissions else roles


CheckAdminDep = Annotated[bool, Depends(check_admin_user)]
CurrentUserDep = Annotated[User, Depends(get_current_active_user)]

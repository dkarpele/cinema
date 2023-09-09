from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, constr
from core import config

password_regex = "^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$"


class UserEmail(BaseModel):
    email: EmailStr


class UserLogin(UserEmail):
    password: constr(min_length=8,
                     max_length=50,
                     regex=password_regex)


class UserData(BaseModel):
    first_name: str = Field(...,
                            description=config.FIRST_NAME_DESC,
                            min_length=3,
                            max_length=50
                            )
    last_name: str = Field(...,
                           description=config.LAST_NAME_DESC,
                           min_length=3,
                           max_length=50)


class UserSignUp(UserLogin, UserData):
    ...


class UserSignUpOAuth(UserLogin, UserData):
    social_id: str
    social_name: str


class UserChangeData(UserLogin):
    email: EmailStr | None
    password: constr(min_length=8,
                     max_length=50,
                     regex=password_regex) | None


class UserResponseData(UserEmail, UserData):
    id: UUID
    disabled: bool = Field(default=False,
                           description="True - inactive, False - active")
    is_admin: bool = Field(default=False,
                           description="True = Admin, False = User")
    roles: set = Field(default=set(),
                       description="List of user's roles")

    class Config:
        orm_mode = True


class UserInDB(UserResponseData):
    # It's a hashed password
    hashed_password: str = Field(default=None,
                                 alias="password")


class UserRoleCreate(BaseModel):
    user_id: UUID
    role_id: UUID


class UserRoleInDB(UserRoleCreate):
    id: UUID


class UserHistory(BaseModel):
    user_id: UUID
    source: str = None
    login_time: datetime


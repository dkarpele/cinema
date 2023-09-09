from uuid import UUID

from pydantic import BaseModel, Field

from core import config


class RoleCreate(BaseModel):
    title: str = Field(...,
                       description=config.ROLE_TITLE_DESC,
                       min_length=3,
                       max_length=50)
    permissions: int = Field(...,
                             description=config.PERMISSIONS_DESC)


class RoleInDB(RoleCreate):
    id: UUID

    class Config:
        orm_mode = True


class RoleToCheck(BaseModel):
    roles: str = Field(...,
                       title="roles",
                       description="A string of roles divided by spaces")

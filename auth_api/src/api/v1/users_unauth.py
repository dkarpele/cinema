from uuid import UUID

from fastapi import APIRouter, status
from models.users import User
from schemas.users import UserResponseData
from services.database import DbDep

from sqlalchemy.future import select

router = APIRouter()


@router.post("/user_ids",
             description="Вся информация о пользователях по списку id",
             response_model=list[UserResponseData],
             status_code=status.HTTP_200_OK)
async def read_users_by_ids(user_ids: list[UUID],
                            db: DbDep) -> list[UserResponseData]:
    async with db:
        users_exists = await db.execute(
            select(User).
            where(User.id.in_(user_ids))
        )
    return users_exists.scalars().all()

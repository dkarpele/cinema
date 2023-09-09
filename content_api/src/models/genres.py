from pydantic import Field

from models.model import Model


class Genre(Model):
    id: str = Field(..., alias="uuid")
    name: str
    description: str | None = None

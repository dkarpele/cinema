from pydantic import Field

from models.model import Model


class Person(Model):
    id: str = Field(..., alias="uuid")
    full_name: str

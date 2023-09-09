from motor.motor_asyncio import AsyncIOMotorClient


class Mongo:
    def __init__(self, client: str):
        self.client = AsyncIOMotorClient(client)


mongo: Mongo | None = None


async def get_mongo() -> Mongo | None:
    return mongo

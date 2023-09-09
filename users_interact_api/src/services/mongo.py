from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import errors
from pymongo.results import DeleteResult

from db.mongo import get_mongo, Mongo
from core.config import mongo_settings
from models.model import Model
from services.exceptions import entity_doesnt_exist


@lru_cache()
def get_mongo_service(
        mongo: Mongo = Depends(get_mongo)) -> Mongo:
    return mongo


MongoDep = Annotated[Mongo, Depends(get_mongo_service)]

MAX_PAGE_SIZE = 10


async def insert_data(
        db: AsyncIOMotorClient,
        insert: Model | dict,
        collection: str,
) -> None:
    """Save doc in Mongo db
    Args:
        :param db: MongoDB
        :param insert: Document to insert
        :param collection: Collection name
    """
    db_name = mongo_settings.db
    db = db.client[db_name]
    try:
        await db[collection].insert_one(jsonable_encoder(insert))
    except errors.PyMongoError as err:
        raise entity_doesnt_exist(err)


async def update_data(
        db: AsyncIOMotorClient,
        query: dict,
        update: dict,
        collection: str,
) -> None:
    """Save doc in Mongo db
    Args:
        :param db: MongoDB
        :param update: Document to upload
        :param query: document to match
        :param collection: Collection name
    """
    db_name = mongo_settings.db
    db = db.client[db_name]
    try:
        await db[collection].update_one(query,
                                        {"$set": update},
                                        upsert=True)
    except errors.PyMongoError as err:
        raise entity_doesnt_exist(err)


async def get_data(
        db: AsyncIOMotorClient,
        query: dict | str,
        collection: str,
        projection: dict | None = None,
        sort: tuple | None = None,
        page: int | None = None,
        size: int | None = None
) -> list:
    """Get doc from Mongo db
    Args:
        :param page: page number
        :param size: page size
        :param sort: tuple = ('sort_by', 1 or -1 for asc or desc)
        :param projection: which fields are returned in the matching documents.
        :param db: MongoDB
        :param query: Request to find
        :param collection: Collection name
    """
    if not sort:
        sort = ('_id', 1)

    if page and size:
        offset = (page * size) - size
    elif page and not size:
        size = MAX_PAGE_SIZE
        offset = (page * size) - size
    elif not page and size:
        offset = 0
    else:
        offset = 0
        size = MAX_PAGE_SIZE

    db_name = mongo_settings.db
    db = db.client[db_name]

    res = (db[collection].
           find(query, projection).
           sort(*sort).
           skip(offset).
           limit(size))

    documents_list = []
    async for document in res:
        try:
            document['_id'] = str(document['_id'])
        except KeyError:
            pass
        documents_list.append(document)

    return documents_list


async def delete_data(
        db: AsyncIOMotorClient,
        document: Model | dict,
        collection: str,
) -> DeleteResult:
    """Delete doc from collection in Mongo db
    Args:
        :param db: MongoDB
        :param document: Document to delete
        :param collection: Collection name
    """
    db_name = mongo_settings.db
    db = db.client[db_name]
    try:
        res = await db[collection].delete_one(jsonable_encoder(document),)
    except errors.PyMongoError as err:
        raise entity_doesnt_exist(err)
    return res


async def get_aggregated(
        db: AsyncIOMotorClient,
        query: dict | str | list,
        collection: str,
) -> list:
    """Get aggregated doc from Mongo db
    Args:
        :param db: MongoDB
        :param query: Request to find
        :param collection: Collection name
    """
    db_name = mongo_settings.db
    db = db.client[db_name]
    res = db[collection].aggregate(query,)
    documents_list = []
    async for document in res:
        try:
            document['_id'] = str(document['_id'])
        except KeyError:
            pass
        documents_list.append(document)

    return documents_list


async def get_count(
        db: AsyncIOMotorClient,
        query: dict | str | list,
        collection: str,
) -> list:
    """Get doc's count from Mongo db
    Args:
        :param db: MongoDB
        :param query: Request to find
        :param collection: Collection name
    """
    db_name = mongo_settings.db
    db = db.client[db_name]
    count = await db[collection].count_documents(query)

    return count

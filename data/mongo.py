from flask import g
from pymongo import MongoClient

import settings as s

class MongoDBClient:
    _client = None

    @staticmethod
    def get_client():
        if MongoDBClient._client is None:
            MongoDBClient._client = MongoClient(s.MONGO_URI)
        return MongoDBClient._client


def get_db(db_name: str):
    # if 'db' not in g:
    #     g.db = MongoDBClient.get_client()[db_name]
    # return g.db
    return MongoDBClient.get_client()[db_name]


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.client.close()
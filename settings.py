from packaging import version
from pymongo import MongoClient

import openai


MONGO_CLIENT = MongoClient('mongodb://localhost:27017/')
DB = MONGO_CLIENT['fitness_db']
USERS_COLLECTION = DB['users']
PROGRESS_COLLECTION = DB['progress']
INTERACTION_LOG_COLLECTION = DB['interaction_logs']
ASSISTANTS_COLLECTION = DB['assistants']
REQUIRED_VERSION = version.parse("1.1.1")
CURRENT_VERSION = version.parse(openai.__version__)
OPENAI_API_KEY = "KEY"

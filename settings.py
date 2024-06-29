""" 
Settings file to manage the env variables or variables 
used around the solution in runtime 
"""
import os

import openai
from packaging import version

MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_URI = f"mongodb+srv://admin:{MONGO_PASSWORD}@cluster0.fizvnzt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_DB = "fitness_db"
REQUIRED_VERSION = version.parse("1.1.1")
CURRENT_VERSION = version.parse(openai.__version__)
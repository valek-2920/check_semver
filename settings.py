""" 
Settings file to manage the env variables or variables 
used around the solution in runtime 
"""
import os.path

import openai
from packaging import version

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "fitness_db"
REQUIRED_VERSION = version.parse("1.1.1")
CURRENT_VERSION = version.parse(openai.__version__)
OPENAI_API_KEY = "sk-proj-HD5DZnNoQwsKDzQltJ9VT3BlbkFJbY0gjMbKqWV6R1W62pwJ"
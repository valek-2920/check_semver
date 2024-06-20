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
OPENAI_API_KEY = ""

REPORT_ASSISTANT_PATH = os.path.abspath(os.path.join("assets", "report_assistant.json"))

""" 
Settings file to manage the env variables or variables 
used around the solution in runtime 
"""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
DEBUG = os.getenv("DEBUG").upper() == "TRUE"
MONGO_DB = "fitness_db"

"""
Module created to run and validate the functionality of User Report Generator
"""
from models.reports import ReportGenerator
from openai import OpenAI

import settings as s


def test_user_report(user_id: str):
    client = OpenAI(api_key=s.OPENAI_API_KEY, default_headers={"OpenAI-Beta": "assistants=v2"})
    generator = ReportGenerator(client, "admin")
    generator.start_assistant_generator()

    conversation_col = generator.db["conversation"]
    conversation = conversation_col.find_one({"user_id": user_id})
    chat = str(conversation["messages"])

    report = generator.start_report_generation(chat)

    return report


if __name__ == "__main__":
    print(test_user_report("user_71445897"))

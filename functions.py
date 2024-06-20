import json
import os
import settings as s
from openai import OpenAI

from prompts import user_profile_generation

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]


def create_report_assistant(client: OpenAI):
    if os.path.exists(s.REPORT_ASSISTANT_PATH):
        with open(s.REPORT_ASSISTANT_PATH, "r") as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data["assistant_id"]
            print("Loaded existing assistant ID.")
    else:
        print("Creating assistant")
        assistant = client.beta.assistants.create(
            # Change prompting in prompts.py file
            instructions=user_profile_generation,
            model="gpt-4-1106-preview",
            tools=[
                {"type": "retrieval"},  # This adds the knowledge base as a tool
                # {
                #     "type": "function",  # This adds the lead capture as a tool
                #     "function": {
                #         "name": "create_lead",
                #         "description":
                #         "Capture lead details and save to Airtable.",
                #         "parameters": {
                #             "type": "object",
                #             "properties": {
                #                 "name": {
                #                     "type": "string",
                #                     "description": "Full name of the lead."
                #                 },
                #                 "phone": {
                #                     "type":
                #                     "string",
                #                     "description":
                #                     "Phone number of the lead including country code."
                #                 }
                #             },
                #             "required": ["name", "phone"]
                #         }
                #     }
                # }
            ],
        )

        # Create a new assistant.json file to load on future runs
        with open(s.REPORT_ASSISTANT_PATH, "w") as file:
            json.dump({"assistant_id": assistant.id}, file)
            print("Created a new assistant and saved the ID.")

        assistant_id = assistant.id

    return assistant_id




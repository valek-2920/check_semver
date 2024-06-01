import json
import requests
import os
from openai import OpenAI
from prompts import assistant_instructions

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']

client = OpenAI(api_key=OPENAI_API_KEY)

def create_assistant(client):
    assistant_file_path = 'assistant.json'

    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, 'r') as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data['assistant_id']
            print("Loaded existing assistant ID.")
    else:
        print("Creating assistant")
        print(assistant_instructions)
        assistant = client.beta.assistants.create(
            # Change prompting in prompts.py file
            instructions=assistant_instructions,
            model="gpt-4-1106-preview",
            tools=[
                {
                    "type":
                    "retrieval"  # This adds the knowledge base as a tool
                },
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
            ])

        # Create a new assistant.json file to load on future runs
        with open(assistant_file_path, 'w') as file:
            json.dump({'assistant_id': assistant.id}, file)
            print("Created a new assistant and saved the ID.")

        assistant_id = assistant.id

    return assistant_id

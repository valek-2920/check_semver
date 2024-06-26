""" TODO: Create docstring """
from data.mongo import get_db
from datetime import datetime
import time
from openai import OpenAI
from prompts import user_profile_generation, factory_generation_instructions

import settings as s


class ReportGenerator:
    def __init__(self, client: OpenAI, user_id: str):
        self.ai_model = "gpt-4-1106-preview"
        self.client = client
        self.user_id = user_id
        self.run_id = None
        self.thread_id = None
        self.db = get_db(s.MONGO_DB)
        self.assistant_col = self.db["assistants"]
        self.assistant_id = self.get_or_create_assistant()

    def get_or_create_assistant(self):
        """
        Create a new assistant for the instance, and
        save its information in "assistant.json" file

        :return: assistant ID
        """
        assistant = self.assistant_col.find_one({"user_id": self.user_id})

        if assistant:
            # print("Loaded existing assistant ID and thread ID for user:", self.user_id)
            self.thread_id = assistant.get('thread_id')
            return assistant['assistant_id']
        else:
            # print(f"Creating assistant for user {self.user_id}...")
            assistant = self.client.beta.assistants.create(
                name="Fitness Trainer Chatbot",
                model=self.ai_model,
                instructions=user_profile_generation,
                tools=[{'type': 'retrieval'}]
            )
            assistant_data = {
                'user_id': self.user_id,
                'assistant_id': assistant.id,
                'model': self.ai_model,
                'instructions': user_profile_generation,
                'tools': [{'type': 'retrieval'}],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            self.assistant_col.insert_one(assistant_data)
            return assistant.id

    def start_assistant_generator(self):
        """ TODO: Create docstring """
        try:
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id
        except Exception as e:
            print(f"There was a problem with the creation of a new thread, error {e}")

    def start_report_generation(self, chat: str):
        """ TODO: Create docstring """
        instructions = factory_generation_instructions\
            .replace("[CHAT]", chat)
        self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=instructions
        )
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )
        self.run_id = run.id

        time.sleep(15)

        answer = self.check_run_status()

        if answer:
            if answer == "Timeout":
                print("Timeout error")
                return
            print(answer)

    def check_run_status(self):
        """ Check the current status of the assistant, and it's answer """
        if not self.thread_id or not self.run_id:
            print("Error: Missing thread_id or run_id in current chat, please start again the process.")
            return

        start_time = time.time()
        while time.time() - start_time < 8:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=self.run_id
            )
            # print("Checking run status:", run_status.status)

            if run_status.status == 'completed':
                messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
                message_content = messages.data[0].content[0].text
                annotations = message_content.annotations

                for annotation in annotations:
                    message_content.value = message_content.value.replace(
                        annotation.text, '')

                # print("Run completed!")
                return message_content.value

            time.sleep(1)

        print("Run timed out")
        return "Timeout"


if __name__ == "__main__":
    client = OpenAI(api_key=s.OPENAI_API_KEY, default_headers={"OpenAI-Beta": "assistants=v2"})
    generator = ReportGenerator(client, "admin")
    generator.start_assistant_generator()

    user_id = "user_71445897"
    conversation_col = generator.db["conversation"]
    conversation = conversation_col.find_one({"user_id": user_id})
    chat = str(conversation["messages"])

    generator.start_report_generation(chat)


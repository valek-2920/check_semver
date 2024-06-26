import time
from datetime import datetime

from openai import OpenAI

import settings as s
from prompts import assistant_instructions
from data.mongo import get_db


class TrainerGenerator:
    """ Class to initiate the AI assistant for the users. """

    def __init__(self, client: OpenAI, user_id: str):
        self.ai_model = "gpt-4-1106-preview"
        self.is_user_new = True
        self.client = client
        self.user_id = user_id
        self.run_id = None
        self.thread_id = None
        self.db = get_db(s.MONGO_DB)
        self.assistant_col = self.db["assistants"]
        self.conversation_col = self.db["conversation"]
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
                instructions=assistant_instructions,
                tools=[{'type': 'retrieval'}]
            )
            assistant_data = {
                'user_id': self.user_id,
                'assistant_id': assistant.id,
                'model': self.ai_model,
                'instructions': assistant_instructions,
                'tools': [{'type': 'retrieval'}],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            self.assistant_col.insert_one(assistant_data)
            return assistant.id

    def start_conversation(self):
        """
        Initiate the conversation with the assistant generated and save its ID
        """
        conversation = self.conversation_col.find_one({"user_id": self.user_id})

        if conversation:
            self.thread_id = conversation["thread_id"]
            self.run_id = conversation["run_id"]
            self.is_user_new = False
        else:
            try:
                thread = self.client.beta.threads.create()
                conversation_data = {
                    'user_id': self.user_id,
                    'assistant_id': self.assistant_id,
                    'thread_id': thread.id,
                    'messages': [],
                    'run_id': None,
                    'status': 'in_progress',
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }

                self.thread_id = thread.id
                self.conversation_col.insert_one(conversation_data)
                self.assistant_col.update_one(
                    {"user_id": self.user_id},
                    {"$set": {"thread_id": self.thread_id, "updated_at": datetime.now()}}
                )
            except Exception as e:
                print(f"There was a problem with the creation of a new thread, error {e}")

    def chat(self, message: str):
        """
        Send the response or the first message to the assistant in order
        to continue/start the conversation
        """
        if not self.thread_id:
            print("Error: Missing thread_id in chat, please start a new conversation")
            return

        # print(f"Received message for thread ID: {self.thread_id} with message: {message}")
        self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=message
        )
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )
        self.run_id = run.id        
        self.conversation_col.update_one(
            {"user_id": self.user_id, "thread_id": self.thread_id},
            {"$push": {"messages": {"role": "user", "content": message}},
            "$set": {"run_id": self.run_id, "updated_at": datetime.now()}}
        )
        # print("Run started with ID:", self.run_id)

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
                    
                self.conversation_col.update_one(
                    {"user_id": self.user_id, "thread_id": self.thread_id},
                    {"$push": {"messages": {"role": "assistant", "content": message_content.value}},
                    "$set": {"status": "completed", "updated_at": datetime.now()}}
                )

                # print("Run completed!")
                return message_content.value

            time.sleep(1)

        print("Run timed out")
        return "Timeout"


def get_non_empty_input(prompt):
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        print("Input cannot be empty. Please try again.")


if __name__ == '__main__':
    whatsapp_number = get_non_empty_input("Enter your WhatsApp number: ")
    user_id = f"user_{whatsapp_number}"
    db = get_db(s.MONGO_DB)
    user_data = {
        "user_id": user_id,
        "whatsapp_number": whatsapp_number,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    db["users"].update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)

    trainer = TrainerGenerator(
        OpenAI(api_key=s.OPENAI_API_KEY, default_headers={"OpenAI-Beta": "assistants=v2"}),
        user_id)

    trainer.start_conversation()

    if trainer.is_user_new:
        initial_message = get_non_empty_input("Welcome to your personal fit trainer, which are your concerns? ")
    else:
        initial_message = get_non_empty_input("")

    trainer.chat(initial_message)

    while True:
        bot_answer = trainer.check_run_status()

        if bot_answer:
            if bot_answer == "Timeout":
                continue

            print(bot_answer)
            user_answer = get_non_empty_input("")

            if user_answer.lower() == "exit":
                print("Exiting...")
                break

            trainer.chat(user_answer)
        else:
            print("There was a problem with the answer, try again later.")



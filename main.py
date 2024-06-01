from datetime import datetime
from openai import OpenAI
from prompts import assistant_instructions

import openai
import settings as s
import time
import re


if s.CURRENT_VERSION < s.REQUIRED_VERSION:
    raise ValueError(
        f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
    )
else:
    print("OpenAI version is compatible.")


class TrainerGenerator:
    """ TODO: Create docstring """

    def __init__(self, client: OpenAI, user_id: str):
        self.ai_model = "gpt-4-1106-preview"
        self.client = client
        self.user_id = user_id
        self.run_id = None
        self.thread_id = None
        self.is_new_user = True
        self.assistant_id = self.get_or_create_assistant()

    def get_or_create_assistant(self):
        """
        Create a new assistant for the instance, and
        save its information in "assistant.json" file

        :return: assistant ID
        """
        assistant = s.ASSISTANTS_COLLECTION.find_one({"user_id": self.user_id})

        if assistant:
            self.is_new_user = False
            print("Loaded existing assistant ID and thread ID for user:", self.user_id)
            self.thread_id = assistant.get('thread_id')
            return assistant['assistant_id']
        else:
            print(f"Creating assistant for user {self.user_id}...")
            assistant = self.client.beta.assistants.create(
                name="Fitness Trainer Chatbot",
                model=self.ai_model,
                instructions=assistant_instructions,
                tools=[{'type': 'retrieval'}]
            )
            assistant_data = {
                'user_id': self.user_id,
                'assistant_id': assistant.id,
                'thread_id': None  # Will be updated once the conversation starts
            }
            s.ASSISTANTS_COLLECTION.insert_one(assistant_data)
            return assistant.id

    def start_conversation(self):
        """
        Initiate the conversation with the assistant generated and save its ID
        """
        if not self.thread_id:
            try:
                thread = self.client.beta.threads.create()
                self.thread_id = thread.id
                s.ASSISTANTS_COLLECTION.update_one(
                    {"user_id": self.user_id},
                    {"$set": {"thread_id": self.thread_id}}
                )
                print("New conversation started with thread ID:", thread.id)
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

        print(f"Received message for thread ID: {self.thread_id} with message: {message}")
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
        print("Run started with ID:", self.run_id)

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
            print("Checking run status:", run_status.status)

            if run_status.status == 'completed':
                messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
                message_content = messages.data[0].content[0].text
                annotations = message_content.annotations

                for annotation in annotations:
                    message_content.value = message_content.value.replace(
                        annotation.text, '')

                print("Run completed!")
                return message_content.value

            time.sleep(1)

        print("Run timed out")
        return "Timeout"

    def store_user_data(self, topic, answer):
        user_data = {'user_id': self.user_id}
        data_retrieved = s.USERS_COLLECTION.find_one(user_data)

        if data_retrieved:
            filter_query = {'_id': data_retrieved["_id"]}
            update_operation = {'$set': {question: answer}}

            result = s.USERS_COLLECTION.update_one(filter_query, update_operation, upsert=False)

            if result.matched_count > 0:
                print("Success ")
            else:
                print(f"There was an error, result {result}")
        else:
            s.USERS_COLLECTION.insert_one(user_data)

    def store_progress_data(self, weight, body_fat_percentage):
        progress_data = {
            'user_id': self.user_id,
            'date': datetime.utcnow(),
            'weight': weight,
            'body_fat_percentage': body_fat_percentage
        }
        s.PROGRESS_COLLECTION.insert_one(progress_data)

    def store_interaction_log(self, message, response):
        log_data = {
            'user_id': self.user_id,
            'timestamp': datetime.utcnow(),
            'message': message,
            'response': response
        }
        s.INTERACTION_LOG_COLLECTION.insert_one(log_data)


def get_non_empty_input(prompt):
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        print("Input cannot be empty. Please try again.")


def extract_question(text):
    # Define the pattern to match the text between [START of question] and [END of question]
    pattern = r'\[START of question\](.*?)\[END of question\]'

    # Use re.search to find the pattern in the text
    match = re.search(pattern, text)

    # If a match is found, return the captured group (the question)
    if match:
        return match.group(1).strip()
    else:
        return None


def clean_answer(answer: str):
    return answer


if __name__ == '__main__':
    whatsapp_number = get_non_empty_input("Enter your WhatsApp number: ")
    user_id = f"user_{whatsapp_number}"
    trainer = TrainerGenerator(
        OpenAI(api_key=s.OPENAI_API_KEY, default_headers={"OpenAI-Beta": "assistants=v2"}),
        user_id)
    trainer.start_conversation()

    initial_message = get_non_empty_input("Welcome to your personal fit trainer, which are your concerns? ")
    trainer.chat(initial_message)

    while True:
        bot_answer = trainer.check_run_status()

        if bot_answer:
            if bot_answer == "Timeout":
                continue

            user_answer = get_non_empty_input("")

            if user_answer.lower() == "exit":
                print("Exiting...")
                break

            question = extract_question(bot_answer)

            if question:
                user_answer = clean_answer(user_answer)
                trainer.store_user_data(question, user_answer)

            trainer.chat(user_answer)
        else:
            print("There was a problem with the answer, try again later.")



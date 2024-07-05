from openai import OpenAI

from data.mongo import get_db
from datetime import datetime

from models.trainer import TrainerGenerator
from utils.utils import get_non_empty_input

import settings as s


def test_trainer(whatsapp_number: str):
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


if __name__ == "__main__":
    phone_number = get_non_empty_input("Enter your WhatsApp number: ")
    test_trainer(phone_number)

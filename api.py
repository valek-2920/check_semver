import os
from flask import Flask, request, jsonify
import openai
from openai import OpenAI
from main import TrainerGenerator

from packaging import version
from data.mongo import close_db

required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

if current_version < required_version:
    raise ValueError(
        f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
    )
else:
    print("OpenAI version is compatible.")


def create_app():
    """
    Creates the Flask app instance

    :return: Flask app instance
    """
    app = Flask(__name__)

    @app.teardown_appcontext
    def teardown_db(exception):
        close_db()

    return app

app = create_app()
client = OpenAI(api_key=OPENAI_API_KEY)

# Create thread
@app.route("/start", methods=["GET"])
def start_conversation():
    user_phone_number = request.headers.get('User-Phone-Number')

    if not user_phone_number:
        print("Error: Missing user_phone_number in /chat")
        return jsonify({"error": "Missing user_phone_number"}), 400

    trainer = TrainerGenerator(client=client, user_id=user_phone_number)
    trainer.start_conversation()

    print("New conversation started with thread ID:", trainer.thread_id)
    return jsonify({"thread_id": trainer.thread_id})


# Start run
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    thread_id = data.get("thread_id")
    user_input = data.get("message", "")

    user_phone_number = request.headers.get('User-Phone-Number')

    if not user_phone_number:
        print("Error: Missing user_phone_number in /chat")
        return jsonify({"error": "Missing user_phone_number"}), 400

    if not thread_id:
        print("Error: Missing thread_id in /chat")
        return jsonify({"error": "Missing thread_id"}), 400
    print("Received message for thread ID:", thread_id, "Message:", user_input)

    trainer = TrainerGenerator(client=client, user_id=user_phone_number)
    trainer.chat(message=user_input)

    print("Run started with ID:", trainer.run_id)
    return jsonify({"run_id": trainer.run_id})


# Check status of run
@app.route("/check", methods=["POST"])
def check_run_status():
    data = request.json
    thread_id = data.get("thread_id")
    run_id = data.get("run_id")

    if not thread_id or not run_id:
        print("Error: Missing thread_id or run_id in /check")
        return jsonify({"response": "error"})

    user_phone_number = request.headers.get('User-Phone-Number')

    if not user_phone_number:
        print("Error: Missing user_phone_number in /chat")
        return jsonify({"error": "Missing user_phone_number"}), 400
    
    trainer = TrainerGenerator(client=client, user_id=user_phone_number)
    trainer.thread_id = thread_id
    trainer.run_id = run_id

    message = trainer.check_run_status()

    if("Timeout" in message):
         return jsonify({"response": message})

    return jsonify({"response": message, "status": "completed"})


# Get user reports
@app.route("/user/reports", methods=["GET"])
def get_user_reports():
    return jsonify({"response": "user_reports"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

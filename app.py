import os
from flask import Flask, request, jsonify, g
import openai
from openai import OpenAI
from main import TrainerGenerator

from packaging import version
from data.mongo import close_db

required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if current_version < required_version:
    raise ValueError(
        f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
    )
else:
    print("OpenAI version is compatible.")


user_instances = {}


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

def get_user_instance(user_id):
    """Retrieve or create an instance for the given user_id."""
    if user_id not in user_instances:
        user_instances[user_id] = TrainerGenerator(client=g.openai_client, user_id=user_id)
    return user_instances[user_id]


@app.before_request
def before_request():
    """Store the user instance in Flask's g object before each request."""
    user_id = f"user_{request.headers.get('User-Phone-Number')}"
    g.openai_client = OpenAI(api_key=OPENAI_API_KEY)

    if user_id:
        g.user_instance = get_user_instance(user_id)
    else:
        return jsonify({"error": "User-Phone-Number header is missing"}), 400


# Create thread
@app.route("/start", methods=["GET"])
def start_conversation():
    user_instance = g.user_instance
    user_instance.start_conversation()

    print("New conversation started with thread ID:", user_instance.thread_id)
    return jsonify({"thread_id": user_instance.thread_id})


# Start run
@app.route("/chat", methods=["POST"])
def chat():
    user_instance = g.user_instance
    data = request.json
    thread_id = data.get("thread_id")
    user_input = data.get("message", "")

    if not thread_id:
        print("Error: Missing thread_id in /chat")
        return jsonify({"error": "Missing thread_id"}), 400

    print("Received message for thread ID:", thread_id, "Message:", user_input)
    user_instance.chat(message=user_input)

    print("Run started with ID:", user_instance.run_id)
    return jsonify({"run_id": user_instance.run_id})


# Check status of run
@app.route("/check", methods=["POST"])
def check_run_status():
    user_instance = g.user_instance
    data = request.json
    thread_id = data.get("thread_id")
    run_id = data.get("run_id")

    if not thread_id or not run_id:
        print("Error: Missing thread_id or run_id in /check")
        return jsonify({"error": "There is no thread_id nor run_id"}), 400

    while True:
        message = user_instance.check_run_status()

        if message:
            if "Timeout" in message:
                continue
            return jsonify({"response": message, "status": "completed"})
        else:
            return jsonify({"Error": "There was a problem generating the answer, try again later"}), 500


# Get user reports
@app.route("/user/reports", methods=["GET"])
def get_user_reports():
    return jsonify({"response": "user_reports"})


if __name__ == "__main__":
    app.run()

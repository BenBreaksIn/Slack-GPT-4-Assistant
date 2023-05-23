import json
import re
import time
import os
import dotenv
import pdfplumber  # PDF extraction library
import tempfile  # For creating temporary files
import asyncio  # For running blocking IO in a separate thread
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, request, make_response

# Load environment variables from .env file
dotenv.load_dotenv()

# Set API key and endpoint
api_key = os.environ.get('OPENAI_API_KEY')
api_url = "https://api.openai.com/v1/chat/completions"

# Initialize Slack client
slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')
client = WebClient(token=slack_bot_token)

# Create Flask server
app = Flask(__name__)

# Rate limiting
user_cooldowns = {}


def preprocess_code(code):
    # Remove any non-alphanumeric characters
    code = re.sub(r'\W+', ' ', code)

    # Remove any placeholder API keys
    code = re.sub(r'\b[a-zA-Z0-9_]{32}\b', 'API_KEY', code)

    return code


async def send_request(prompt):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {
        "model": "gpt-4",
        "messages": [{"role": "system", "content": "You are talking to Chloe, an AI assistant."},
                     {"role": "user", "content": prompt}],
        "max_tokens": 8000,
        "n": 1,
        "temperature": 0.8
    }
    json_data = json.dumps(data, ensure_ascii=False).encode('utf8')
    escaped_data = json_data.decode('utf8')

    async with aiohttp.ClientSession() as session:
        response = None
        while True:
            try:
                async with session.post(api_url, headers=headers, data=escaped_data) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientResponseError as e:
                if response and response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", "1"))
                    print(f"Rate limited. Retrying in {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                else:
                    print(f"Error occurred: {e}")
                    return None
            except Exception as e:
                print(f"Error occurred: {e}")
                return None


def parse_response(response_json):
    if response_json is None:
        return "An error occurred while processing your request. Please try again."
    try:
        return response_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return "An error occurred while processing your request. Please try again."


async def gpt4_response(prompt):
    prompt = preprocess_code(prompt)
    response_json = await send_request(prompt)
    return parse_response(response_json)


def extract_text_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        return ' '.join(page.extract_text() for page in pdf.pages)


# Cooldown check
def is_on_cooldown(user_id):
    cooldown_time = 7  # Seconds
    if user_id in user_cooldowns:
        remaining_time = cooldown_time - (time.time() - user_cooldowns[user_id])
        if remaining_time > 0:
            return remaining_time
    user_cooldowns[user_id] = time.time()
    return False


# Handle incoming events
@app.route("/events", methods=["POST"])
def handle_event():
    payload = request.get_json()
    event = payload.get("event", {})

    # Only handle message events
    if event.get("type") == "message":
        channel_id = event.get("channel")
        user_id = event.get("user")

        remaining_time = is_on_cooldown(user_id)
        if remaining_time:
            client.chat_postMessage(
                channel=channel_id,
                text=f"You're on cooldown. Please wait {remaining_time:.0f} seconds."
            )
            return make_response("", 200)

        prompt = event.get("text")
        # Handle files attached in message
        # Only handling PDFs in this case as an example
        files = event.get("files", [])
        for file in files:
            if file.get("filetype") == "pdf":
                url_private = file.get("url_private")
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                client.files_download(url=url_private, filename=temp_file.name)
                temp_file.close()  # Close the file before deleting it
                extracted_text = extract_text_from_pdf(temp_file.name)
                os.unlink(temp_file.name)  # Delete temp file
                prompt += ' ' + extracted_text

        response = asyncio.run(gpt4_response(prompt))
        try:
            client.chat_postMessage(
                channel=channel_id,
                text=response
            )
        except SlackApiError as e:
            print(f"Error posting message: {e}")
        user_cooldowns[user_id] = time.time()

    return make_response("", 200)


# For handling Slack's url_verification event
@app.route("/events", methods=["GET", "POST"])
def handle_verification():
    payload = request.get_json()
    if payload.get('type') == 'url_verification':
        return make_response(payload.get('challenge'), 200, {'content_type': 'text/plain'})


# Start the Flask server
if __name__ == "__main__":
    app.run(port=3000)

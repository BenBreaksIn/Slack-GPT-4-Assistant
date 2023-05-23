
# Slack GPT-4 Assistant

This is a Slack bot powered by OpenAI's GPT-4. The bot can respond to messages and extract text from attached PDF files.

## Prerequisites

- Python 3.7 or above
- [slack_sdk](https://slack.dev/python-slack-sdk/)
- [Flask](https://flask.palletsprojects.com/en/2.0.x/)
- [aiohttp](https://docs.aiohttp.org/en/stable/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [pdfplumber](https://pypi.org/project/pdfplumber/)

You can install the necessary libraries using pip:

```sh
pip install slack_sdk flask aiohttp python-dotenv pdfplumber
```

## Setup

1. **Get your OpenAI API key.** Sign up for an account at [OpenAI](https://www.openai.com/). Navigate to the API section to find your API key.

2. **Set up a new Slack app.** Go to your [Slack Apps page](https://api.slack.com/apps) and click "Create New App". Name it, select your workspace, and click "Create App".

3. **Enable event subscriptions.** In your app settings, navigate to "Event Subscriptions" and toggle "Enable Events" on. You'll need to provide a request URL, which is the URL of the server where you're running your bot, with the `/events` endpoint. For local development, you can use services like [ngrok](https://ngrok.com/).

4. **Subscribe to bot events.** While in the "Event Subscriptions" page, scroll down to "Subscribe to bot events" and click "Add Bot User Event". Add the `message.channels` and `message.im` events. This will allow your bot to read messages from channels and direct messages.

5. **Install your app to your workspace.** Go to "Install App" in your app settings and click "Install App to Workspace". You'll be asked to authorize the app in your workspace and, once authorized, you'll be provided with a "Bot User OAuth Access Token". 

6. **Set up your environment variables.** In the root directory of your project, create a `.env` file and add the following:

    ```
    OPENAI_API_KEY=your_openai_api_key
    SLACK_BOT_TOKEN=your_slack_bot_token
    ```

    Replace `your_openai_api_key` and `your_slack_bot_token` with your actual OpenAI API key and Slack bot token.

7. **Run your bot.** Run the script with:

    ```sh
    python slack_bot.py
    ```

Your bot should now be running in your workspace and responding to messages directed to it. Enjoy interacting with your AI-powered bot!

---

Remember, this is a simple setup and won't cover things like error handling and deployment. You may need to adjust the setup based on your environment and use case.

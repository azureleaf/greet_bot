import os
import sys
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# Instantiate Flask class
# Give the name of the current module to the constructor
app = Flask(__name__)

# Get keys from environment variables
channel_secret = os.environ['LINE_CHANNEL_SECRET']
channel_access_token = os.environ['LINE_CHANNEL_ACCESS_TOKEN']

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

# Instantiate classes of linebot package
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/")
def hello_world():
    """Used to test if Flask
        Args: none
        Returns: string
    """
    return "hello world!"


@app.route("/callback", methods=['POST'])
def callback():
    """ Validate the request content
        Args: none
        Returns: string
            Http 400 message, or "OK"
    """
    # get X-Line-Signature header value
    # Seemingly request from the LINE has signature
    # for authorized secure communication
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        # Abort if the calculated value isn't identical with the signature
        # abort() is the internal function in Flask
        # 400 returns "The browser (or proxy) sent a request
        #   that this server could not understand."
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """"""
    line_bot_api.reply_message(
        event.reply_token,  # what's this?
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run()

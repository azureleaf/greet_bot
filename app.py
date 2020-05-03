import os
import sys
from flask import Flask, request, abort
from tools import get_weather, find_closest_stops
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent,
    TextMessage, LocationMessage, TextSendMessage, TemplateSendMessage,
    ButtonsTemplate,
    PostbackAction
)

# Instantiate Flask class
# Give the name of the current module to the constructor
app = Flask(__name__)

# Get keys from environment variables of the server
channel_secret = os.environ['LINE_CHANNEL_SECRET']
channel_access_token = os.environ['LINE_CHANNEL_ACCESS_TOKEN']

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as an environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as an environment variable.')
    sys.exit(1)

# Instantiate classes of linebot package
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/")
def hello_world():
    """Test if the flask is correctly working
        Args: none
        Returns: string
    """
    return "hello world!"


@app.route("/callback", methods=['POST'])
def callback():
    """ Validate the request content
        Args: none
        Returns: string
            Http 400
            "OK"
    """
    # get X-Line-Signature header value
    # Seemingly request from the LINE has signature
    # for authorized secure communication
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)

    # How can I check this log files???
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
    """ Return messages to the LINE user who sent text message
        args: event
        return: void
    """

    # Change reply message from the bot
    # according to the keywords included in the message by user
    if "天気" in event.message.text:
        reply_msgs = get_weather()
        reply_content = []
        for reply_msg in reply_msgs:
            reply_content += [TextSendMessage(text=reply_msg)]
        line_bot_api.reply_message(
            event.reply_token, reply_content
        )
    elif "交通" in event.message.text:
        get_button_template(event)
    else:
        reply_msg = (f"こんにちは！"
                     f"「天気」というと今の仙台の天気と予報をお伝えします。"
                     f"位置情報を投げると、近くの地下鉄駅やバス停を検索しますよ！")
        line_bot_api.reply_message(
            event.reply_token, [TextSendMessage(text=reply_msg)]
        )


@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    """ Return messages to the LINE user who sent geo location
        args: event
        return: void
    """

    lat = event.message.latitude
    lon = event.message.longitude

    stops = find_closest_stops(lat, lon, 0.5)

    reply_msg = ""
    for stop in stops:
        reply_msg += "「" + stop[0] + \
            "」まで" + str(round(stop[1]*1000)) + "メートルです。\n"

    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text="近くにあるバス停はこちらです！"),
            TextSendMessage(text=reply_msg)
        ]
    )


def get_button_template(event):
    buttons_template = ButtonsTemplate(
        title="交通機関を選択",
        text="どれに乗りますか？",
        actions=[
            PostbackAction(label="地下鉄南北線", data="subway_n"),
            PostbackAction(label="地下鉄東西線", data="subway_t"),
            PostbackAction(label="路線バス", data="bus"),
        ]
    )
    template_message = TemplateSendMessage(
        alt_text='ボタン要素',
        template=buttons_template
    )
    line_bot_api.reply_message(event.reply_token, template_message)


if __name__ == "__main__":
    app.run()

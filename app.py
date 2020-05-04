<<<<<<< HEAD
from linebot.models import (
    MessageEvent, PostbackEvent,
    TextMessage, LocationMessage, TextSendMessage, TemplateSendMessage,
    ButtonsTemplate,
    PostbackAction
=======
import os
import sys
from flask import Flask, request, abort
from tools import get_weather, find_closest_stops

from linebot import (
    LineBotApi, WebhookHandler
>>>>>>> 895a1b0751182ddfeba6c44af5e242901bd287d3
)
from linebot.exceptions import (
    InvalidSignatureError
)
<<<<<<< HEAD
from linebot import (
    LineBotApi, WebhookHandler
)
import os
import sys
from flask import Flask, request, abort
from tools import (get_weather,
                   find_closest_stops,
                   find_nearest_station,
                   list_coming_trains,
                   sendai_city_hall
                   )
from datetime import datetime

# Sample position for debugging (global var)
# This will be overwritten by user position
lat = sendai_city_hall["lat"]
lon = sendai_city_hall["lon"]
=======
from linebot.models import (
    MessageEvent, TextMessage, LocationMessage, TextSendMessage,
)
>>>>>>> 895a1b0751182ddfeba6c44af5e242901bd287d3

# Instantiate Flask class
# Give the name of the current module to the constructor
app = Flask(__name__)

# Get keys from environment variables of the server
channel_secret = os.environ['LINE_CHANNEL_SECRET']
channel_access_token = os.environ['LINE_CHANNEL_ACCESS_TOKEN']

if channel_secret is None:
<<<<<<< HEAD
    print('Specify LINE_CHANNEL_SECRET as an environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as an environment variable.')
=======
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
>>>>>>> 895a1b0751182ddfeba6c44af5e242901bd287d3
    sys.exit(1)

# Instantiate classes of linebot package
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/")
def hello_world():
<<<<<<< HEAD
    """Test if the flask is correctly working
=======
    """Used to test if Flask
>>>>>>> 895a1b0751182ddfeba6c44af5e242901bd287d3
        Args: none
        Returns: string
    """
    return "hello world!"


@app.route("/callback", methods=['POST'])
def callback():
    """ Validate the request content
        Args: none
        Returns: string
<<<<<<< HEAD
            Http 400
            "OK"
=======
            Http 400 message, or "OK"
>>>>>>> 895a1b0751182ddfeba6c44af5e242901bd287d3
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
<<<<<<< HEAD
    """ Tell about weather for text message from the user
=======
    """ Return messages to the LINE user who sent text message
>>>>>>> 895a1b0751182ddfeba6c44af5e242901bd287d3
        args: event
        return: void
    """

<<<<<<< HEAD
    reply_msgs = get_weather()
    reply_content = []
    for reply_msg in reply_msgs:
        reply_content += [TextSendMessage(text=reply_msg)]
    line_bot_api.reply_message(
        event.reply_token, reply_content
=======
    # Change reply message from the bot
    # according to the keywords included in the message by user
    if "天気" in event.message.text:
        reply_msg = get_weather()
    else:
        reply_msg = "こんにちは！"

    line_bot_api.reply_message(
        event.reply_token,
        # TextSendMessage(text=event.message.text))
        [
            TextSendMessage(text=reply_msg)
        ]
>>>>>>> 895a1b0751182ddfeba6c44af5e242901bd287d3
    )


@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    """ Return messages to the LINE user who sent geo location
        args: event
        return: void
    """

<<<<<<< HEAD
    global lat, lon
    lat = event.message.latitude
    lon = event.message.longitude

    reply_with_trans_selector(event)


@handler.add(PostbackEvent)
def handle_postback(event):
    """Respond to the button input sent by the user"""

    if event.postback.data == 'subway':
        # Let the user choose the line
        reply_with_line_selector(event)
    elif event.postback.data == 'bus':
        tell_bus_stop(event)
    elif event.postback.data in \
            ["泉中央行", "富沢行", "八木山動物公園行", "荒井行"]:
        tell_station(event, event.postback.data)


def reply_with_trans_selector(event):
    '''Reply with the buttons to choose bus or subway'''
    buttons_template = ButtonsTemplate(
        title="交通機関を選択",
        text="何に乗りますか？",
        actions=[
            PostbackAction(label="地下鉄", data="subway"),
            PostbackAction(label="路線バス", data="bus"),
        ]
    )
    template_message = TemplateSendMessage(
        alt_text='ボタン要素',
        template=buttons_template
    )
    line_bot_api.reply_message(event.reply_token, template_message)


def reply_with_line_selector(event):
    '''Reply with the buttons to choose subway line'''

    buttons_template = ButtonsTemplate(
        title="地下鉄の路線を選択",
        text="どっち方向に行きますか？",
        actions=[
            PostbackAction(label="南北線（泉中央行）", data="泉中央行"),
            PostbackAction(label="南北線（富沢行）", data="富沢行"),
            PostbackAction(label="東西線（動物公園行）", data="八木山動物公園行"),
            PostbackAction(label="東西線（荒井行）", data="荒井行"),
        ]
    )
    template_message = TemplateSendMessage(
        alt_text='ボタン要素',
        template=buttons_template
    )
    line_bot_api.reply_message(event.reply_token, template_message)


def tell_station(event, dst):
    '''Reply to the user with nearest station & schedule of coming trains '''

    now = datetime.now()
    station = find_nearest_station(lat, lon, dst)
    trains_weekday = list_coming_trains(
        now, station["station_name"], dst, False)
    trains_holiday = list_coming_trains(
        now, station["station_name"], dst, True)

    # Message of station name
    sta_msg = f"{station['station_name']}駅まで約{station['meters']}メートルです！"

    # Message of train schedule
    time_msg = dst + "の直近の列車です！\n"
    for (index, trains) in enumerate([trains_weekday, trains_holiday]):
        time_msg += ["平日ダイヤ：", "\n休日ダイヤ："][index]
        for train in trains:
            if len(trains) == 0:
                time_msg = "到着予定の列車はありません。"
            dep_time = train.strftime("\n%H：%M発")
            diff_time = train - now
            time_msg += f"{dep_time}（{str(int(diff_time.seconds / 60))}分後）"

    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text=sta_msg),
            TextSendMessage(text=time_msg)
        ]
    )


def tell_bus_stop(event):
    '''Reply with the text list of nearest bus stops '''

=======
    lat = event.message.latitude
    lon = event.message.longitude

>>>>>>> 895a1b0751182ddfeba6c44af5e242901bd287d3
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


if __name__ == "__main__":
    app.run()

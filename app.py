from linebot.models import (
    MessageEvent, PostbackEvent,
    TextMessage, LocationMessage, TextSendMessage, TemplateSendMessage,
    ButtonsTemplate,
    PostbackAction
)
from linebot.exceptions import (
    InvalidSignatureError
)
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
                   )
from datetime import datetime
import pytz
import json


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
    """ Tell about weather for text message from the user
        args: event
        return: void
    """

    reply_msgs = get_weather()
    reply_content = []
    for reply_msg in reply_msgs:
        reply_content += [TextSendMessage(text=reply_msg)]
    line_bot_api.reply_message(
        event.reply_token, reply_content
    )


@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    """ Reply to the LINE user who sent geo location with buttons
        args: event
        return: void
    """

    lat = event.message.latitude
    lon = event.message.longitude

    reply_with_trans_selector(event, lat, lon)


@handler.add(PostbackEvent)
def handle_postback(event):
    """Respond to the button input sent by the user"""

    # Parse stringified dict
    params = json.loads(event.postback.data)

    if params["btn"] == 'subway':
        reply_with_line_selector(event,
                                 params["lat"],
                                 params["lon"])
    elif params["btn"] == 'bus':
        tell_bus_stop(event,
                      params["lat"],
                      params["lon"])
    elif params["btn"] in \
            ["泉中央行", "富沢行", "八木山動物公園行", "荒井行"]:
        tell_station(event,
                     params["lat"],
                     params["lon"],
                     params["btn"])


def reply_with_trans_selector(event, lat, lon):
    '''Reply with the buttons to choose bus or subway'''

    # Stringify the parameters because
    # postback event can send only one value
    params = {}
    for trans in ["subway", "bus"]:
        params[trans] = json.dumps(
            {
                "lat": lat,
                "lon": lon,
                "btn": trans
            }
        )
        app.logger.info("Stringified: " + params[trans])

    buttons_template = ButtonsTemplate(
        title="交通機関を選択",
        text="何に乗りますか？",
        actions=[
            PostbackAction(label="地下鉄", data=params["subway"]),
            PostbackAction(label="路線バス", data=params["bus"]),
        ]
    )
    template_message = TemplateSendMessage(
        alt_text='交通機関を選択',
        template=buttons_template
    )
    line_bot_api.reply_message(event.reply_token, template_message)


def reply_with_line_selector(event, lat, lon):
    '''Reply with the buttons to choose subway line'''

    # Stringify the parameters because
    # postback event can send only one value
    params = {}
    for dst in ["泉中央行", "富沢行", "八木山動物公園行", "荒井行"]:
        params[dst] = json.dumps(
            {
                "lat": lat,
                "lon": lon,
                "btn": dst
            }
        )

    buttons_template = ButtonsTemplate(
        title="地下鉄の路線を選択",
        text="どっち方向に行きますか？",
        actions=[
            PostbackAction(label="南北線（泉中央行）", data=params["泉中央行"]),
            PostbackAction(label="南北線（富沢行）", data=params["富沢行"]),
            PostbackAction(label="東西線（動物公園行）", data=params["八木山動物公園行"]),
            PostbackAction(label="東西線（荒井行）", data=params["荒井行"]),
        ]
    )
    template_message = TemplateSendMessage(
        alt_text='地下鉄の路線を選択',
        template=buttons_template
    )
    line_bot_api.reply_message(event.reply_token, template_message)


def tell_station(event, lat, lon, dst):
    '''Reply to the user with nearest station & schedule of coming trains '''

    now = datetime.now(pytz.timezone('Asia/Tokyo'))
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
        time_msg += ["\n平日ダイヤ：", "\n\n休日ダイヤ："][index]
        if len(trains) == 0:
            time_msg += "\n到着予定がありません。"
            continue
        for train in trains:
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


def tell_bus_stop(event, lat, lon):
    '''Reply with the text list of nearest bus stops '''

    stops = find_closest_stops(lat, lon, 0.5)

    reply_msg = ""
    for stop in stops:
        reply_msg += "「" + stop[0] + \
            "」まで" + str(round(stop[1]*1000)) + "mです。\n"

    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text="近くにあるバス停はこちらです！"),
            TextSendMessage(text=reply_msg)
        ]
    )


if __name__ == "__main__":
    app.run()

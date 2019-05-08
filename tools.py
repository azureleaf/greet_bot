import urllib.request
import json


def get_weather():
    fetch_data = urllib.request.urlopen(
        'http://api.openweathermap.org/data/2.5/weather?q=Sendai&appid=ef73002b35f939a39e156f73f739a534')
    html = fetch_data.read()

    data_dict = json.loads(html)

    weather = data_dict['weather'][0]['main']
    temp_now = data_dict['main']['temp'] - 273.15
    temp_max = data_dict['main']['temp_max'] - 273.15

    fetch_data.close()

    return "今日の仙台の天気は{}、予想最高気温は{}度です。今の気温は{}度ですね。" \
        .format(weather, str(round(temp_max, 1)), str(round(temp_now, 1)))

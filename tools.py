import urllib.request
import json


def get_weather():
    fetch_data = urllib.request.urlopen(
        'http://api.openweathermap.org/data/2.5/weather?q=Sendai&appid=ef73002b35f939a39e156f73f739a534')
    html = fetch_data.read()

    data_dict = json.loads(html)

    weather = data_dict['weather'][0]['main']
    temp_max = data_dict['main']['temp_max'] - 273.15

    fetch_data.close()

    return "こんにちは。今日の天気は" + weather + "、最高気温は" + temp_max + "です。"

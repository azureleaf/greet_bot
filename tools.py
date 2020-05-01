import urllib.request
import json
import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import closing
from math import sin, cos, sqrt, atan2, radians

# Set user variables
db_path = os.getcwd() + '/busstop.db'

open_weather_api_key = os.environ['OPEN_WEATHER_API_KEY']
open_weather_city_name = "Sendai"

OPENWX = {
    "KEY": os.environ['OPEN_WEATHER_API_KEY'],
    "CITY": "Sendai"
}

# FOR TEST USE: coordinates of some sample points
sendai_city_hall = {
    "lat": 38.2682,
    "lon": 140.8694}
fukushima_city_hall = {
    "lat": 37.7608,
    "lon": 140.4748}


def get_weather():

    # Get current weather & 5 days forecast
    fetch_dict = {}
    for info_type in ["weather", "forecast"]:
        # Retrieve from OpenWeather
        url = 'http://api.openweathermap.org/data/2.5/' \
            + info_type \
            + '?q=' \
            + OPENWX["CITY"] \
            + '&appid=' \
            + OPENWX["KEY"] \
            + '&lang=ja'

        fetch_raw = urllib.request.urlopen(url)  # Access the API
        fetch_html = fetch_raw.read()  # Convert to HTML
        fetch_dict[info_type] = json.loads(fetch_html)  # convert to JSON
        fetch_raw.close()

    # Text messages to return
    msgs = []

    # Current weather
    curr_weather = fetch_dict['weather']['weather'][0]['description']
    curr_temp = fetch_dict['weather']['main']['temp'] - 273.15
    curr_pressure = fetch_dict['weather']['main']['pressure']
    curr_humidity = fetch_dict['weather']['main']['humidity']
    msgs.append(
        (f"今の仙台の天気は{curr_weather}、気温{str(round(curr_temp, 1))}度、"
         f"湿度{curr_humidity}％、"
         f"気圧{curr_pressure}hPaですね。")
    )

    # Forecasted weather
    for forecast in fetch_dict["forecast"]["list"]:
        # Convert string UTC time to JST datetime
        dt_forecast = datetime.strptime(
            forecast["dt_txt"], "%Y-%m-%d %H:%M:%S") + timedelta(hours=9)
        # I don't want 3-hour forecasts;
        # e.g. drop 9:00 & 15:00, leave 12:00 & 18:00
        if dt_forecast.hour % 6 != 0:
            continue
        msgs.append(
            (f'{dt_forecast.hour}時の予報は'
             f'気温が{str(round(forecast["main"]["temp"] - 273.15, 1))}度、'
             f'天気は{forecast["weather"][0]["description"]}です。')
        )
        # I want forecasts [current, 6 hrs, 12 hrs] only
        if len(msgs) == 3:
            break

    return msgs


def find_closest_stops(lat, lon, range_km):
    """Get GPS coordinates, returns bus stops near the point
        Args:
            latutude, longitude (float)
                degrees
        Returns:
            list of the names of the closest bus stops
    """

    try:
        with closing(sqlite3.connect(db_path)) as conn:

            # Search inside the range of the candidates bus stops
            # This range has the rectangular shapes;
            # current position +/- certain distance (here, range_km)
            range_lat = distance_to_degree(
                range_km, lat, lon)["lat_deg"]
            range_lon = distance_to_degree(
                range_km, lat, lon)["lon_deg"]

            c = conn.cursor()

            sql_select = """ SELECT * FROM stops WHERE
                lat > ? - ? AND
                lat < ? + ? AND
                lon > ? - ? AND
                lon < ? + ?
            """
            c.execute(sql_select, (
                lat, range_lat,
                lat, range_lat,
                lon, range_lon,
                lon, range_lon,
            ))

            nearby_stops = c.fetchall()

            # Container of the calculated distances to each bus stop
            distances = {}

            # Note that each stop comes in the format of:
            #   (1234, "仙台駅前", 38.111, 140.111)
            for stop in nearby_stops:
                stop_name = stop[1]
                stop_distance = get_distance(lat, lon, stop[2], stop[3])
                distances[stop_name] = stop_distance

            # Sort dictionary by distance value
            # Here "x" is "(stop_name, distance)",
            # therefore x[1] is distance
            distances_sorted = sorted(distances.items(), key=lambda x: x[1])

            return distances_sorted

    except sqlite3.Error as e:
        print("Error occured in sqlite! :", e.args[0])


def get_distance(lat1_deg, lon1_deg, lat2_deg, lon2_deg):
    ''' Get GPS position of 2 points, returns absolute distance
        Calculation based on Spherical Trigonometry (球面三角法)
        Args:
            lat1_deg, lon1_deg, lat2_deg, lon2_deg (float)
                latitude & coordinates (in degrees) of 2 points
        Return:
            distance in km (float)
    '''

    # Radius of the imaginary Earth
    R = 6573.0

    # Convert from degrees into radians
    lat1_rad = radians(lat1_deg)
    lon1_rad = radians(lon1_deg)
    lat2_rad = radians(lat2_deg)
    lon2_rad = radians(lon2_deg)

    lat_diff = lat2_rad - lat1_rad
    lon_diff = lon2_rad - lon1_rad

    a = sin(lat_diff / 2)**2 + cos(lat1_rad) * \
        cos(lat2_rad) * sin(lon_diff / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance


def distance_to_degree(d_km, lat, lon):
    ''' Mapping distance into degree at the specific geo point
        Args:
            d_km (int)
                distance in kilometers, to be converted into degrees
            lat, lon (float)
                latitude and longitude, in degrees
        Returns:
            dictionary of degrees which is mapped from d_km
            for both latitude degrees & longitude degrees
    '''

    # Move coordinate by 1 degree to check its distance
    lat_km_per_deg = get_distance(
        lat,   lon,
        lat+1, lon)
    lon_km_per_deg = get_distance(
        lat, lon,
        lat, lon+1)

    degrees = {
        "lat_deg": d_km / lat_km_per_deg,
        "lon_deg": d_km / lon_km_per_deg
    }

    return degrees


# For debugging
if __name__ == "__main__":

    print(get_weather())

    print(find_closest_stops(
        sendai_city_hall["lat"],
        sendai_city_hall["lon"],
        0.5))

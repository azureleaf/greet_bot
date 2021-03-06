import urllib.request
import json
import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import closing
from math import sin, cos, sqrt, atan2, radians
import constants
import numpy as np

# Set user variables
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
    curr_humidity = fetch_dict['weather']['main']['humidity']
    msgs.append(
        (f"今の仙台の天気は「{curr_weather}」、気温{str(round(curr_temp, 1))}度、"
         f"湿度{curr_humidity}％ですね。")
    )

    # Forecasted weather
    forecast_msg = "予報は以下のとおりです！"
    for index, forecast in enumerate(fetch_dict["forecast"]["list"]):
        # I need forecasts only for next 24 hours
        if index == 8:
            break

        # Convert string UTC time to JST datetime
        dt_forecast = datetime.strptime(
            forecast["dt_txt"], "%Y-%m-%d %H:%M:%S") + timedelta(hours=9)
        forecast_msg += \
            (f'\n{dt_forecast.strftime("%H")}時に'
             f'{str(round(forecast["main"]["temp"] - 273.15, 1))}度で'
             f'「{forecast["weather"][0]["description"]}」')

    msgs.append(forecast_msg)

    return msgs


def find_closest_stops(lat, lon, range_km):
    """Get GPS coordinates, returns bus stops near the point
        Args:
            latutude, longitude (float)
                degrees
            range_km (float)
                range of search;
                e.g. when 2, search inside 4km * 4km
                square around the point specified
        Returns:
            list of the names of the closest bus stops
    """

    try:
        with closing(sqlite3.connect(constants.DB_PATH)) as conn:

            # Search inside the range of the candidates bus stops
            # This range has the rectangular shapes;
            # current position +/- certain distance (here, range_km)
            range_lat = km2deg(
                range_km, lat, lon)["lat_deg"]
            range_lon = km2deg(
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


def find_nearest_station(lat, lon, dst):
    """Get GPS coordinates, returns bus stops near the point
        Args:
            latutude, longitude (float)
                degrees
            dst (string)
                Destination of the train:
                "泉中央行", "富沢行", "八木山動物公園行", "荒井行"
        Returns:
            dict: nearest station name & distance to it
    """

    # Row factory to get DB content as an array of dict
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    conn = sqlite3.connect(constants.DB_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    line_name = "南北線" if (dst in ["泉中央行", "富沢行"]) else "東西線"
    c.execute("SELECT * FROM stations WHERE line = ?;", [line_name])
    stations = c.fetchall()
    conn.close()

    # Calculate distances to every station
    distances = np.array(
        [get_distance(lat, lon, station["lat"], station["lon"])
         for station in stations]
    )
    nearest_d = np.amin(distances)

    # Index of the station with the minimum distance
    nearest_i = np.where(distances == nearest_d)[0][0]

    return {
        "station_name": stations[nearest_i]["name"],
        "meters": int(round(nearest_d, 2) * 1000)}


def list_coming_trains(dt_now, station_name, dst, isHoliday=False):
    """
    Tells the trains coming.
    Args:
        dt_now (datetime object):
            Reference time to search trains from.
        station_name (string):
            Name of the station in Japanese (e.g. 長町).
        dst (string):
            Destination in Japanese (e.g. 泉中央行).
        isHoliday (bool):
            Tells if it's weekday or holiday.
    Returns:
        (List of datetime object):
            Departure times of the coming trains
            in this / next hour;
            3 trains at most, 0 train at least.
    """
    # Row factory to get DB content as an array of dict
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def list_trains_in_the_hr(timetable, dt):
        hr = str(dt.hour)

        # Unlike datetime lib, timetable use "24:00" notation
        hr = "0" if hr == "24" else hr

        # When it's late night, or no train in the hour
        if (hr not in timetable.keys()) \
                or (len(timetable[hr]) == 0):
            return []

        # Parse string and get list of trains in this hour
        train_mins = timetable[hr].split(",")

        # List trains which comes after the datetime
        return [dt.replace(
            minute=int(train_min), second=0, microsecond=0)
            for train_min in train_mins
            if dt.replace(
            minute=int(train_min), second=0, microsecond=0) >= dt]

    conn = sqlite3.connect(constants.DB_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()

    table_name = "timetable_subway_" + ("holiday" if isHoliday else "weekday")

    # Note that you can't use "?" placeholder for the table name!
    c.execute(
        f"SELECT * FROM {table_name} WHERE sta = ? AND dst = ?;",
        [station_name, dst])
    timetable = c.fetchone()
    conn.close()

    # Get trains which comes in this hour　(00 to 60)
    trains = list_trains_in_the_hr(timetable, dt_now)

    # Search next hour to offer at least 3 coming trains if possible
    if len(trains) < 3:
        trains += list_trains_in_the_hr(
            timetable,
            dt_now.replace(
                minute=0,
                second=0,
                microsecond=0) + timedelta(hours=1))

    # Return 3 trains at most
    return trains[:3]


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


def km2deg(d_km, lat, lon):
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


def wrapper():
    '''Debug'''

    msgs = get_weather()
    for msg in msgs:
        print(msg)

    return

    now = datetime.now()
    now = now.replace(hour=7, minute=58)

    coming_trains = list_coming_trains(now, "長町", "富沢行", False)
    print(coming_trains)

    nearest = find_nearest_station(38.258780, 140.851185, "泉中央行")
    print(nearest)

    print(find_closest_stops(
        sendai_city_hall["lat"],
        sendai_city_hall["lon"],
        0.5))


if __name__ == "__main__":
    wrapper()

'''
Analyze downloaded GPS positions of the subway stations,
save it to SQLite DB
'''

import pandas as pd
import numpy as np
import constants
import json
import sqlite3


def json2df(db_path):
    with open(db_path) as f:
        json_str = f.read()

    df = pd.DataFrame(columns=["line", "name", "lat", "lon"])

    json_loaded = json.loads(json_str)
    for station in json_loaded["features"]:
        station_pos = {}
        if station["properties"]["N02_004"] == "仙台市":
            station_pos["line"] = station["properties"]["N02_003"]
            station_pos["name"] = station["properties"]["N02_005"]
            station_edge_points = np.asarray(
                station["geometry"]["coordinates"])
            [avg_lon, avg_lat] = np.average(station_edge_points, axis=0)
            station_pos["lat"] = round(avg_lat, 5)
            station_pos["lon"] = round(avg_lon, 5)
            df = df.append(station_pos, ignore_index=True)
    return df


if __name__ == "__main__":
    df = json2df(constants.STA_POS_FILE_PATH)

    conn = sqlite3.connect(constants.DB_PATH)

    df.to_sql(
        "stations",
        conn,
        if_exists='replace',
        index=None)

    conn.close()

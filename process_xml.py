import xml.etree.ElementTree as ET
import os
import sqlite3
from contextlib import closing

db_path = os.getcwd() + '/busstop.db'
namespaces = {
    "jps": "http://www.gsi.go.jp/GIS/jpgis/standardSchemas",
    "ksj": "http://nlftp.mlit.go.jp/ksj/schemas/ksj-app",
    "ksjc": "http://nlftp.mlit.go.jp/ksj/schemas/ksj-app-cd",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xlink": "http://www.w3.org/1999/xlink",
    "schemaLocation": "http://nlftp.mlit.go.jp/ksj/schemas/ksj-app \
        KsjAppSchema-P11.xsd",

}

# FOR TEST USE: sample xml file to check the function
# tree = ET.parse('sample.xml')

tree = ET.parse('P11-10_04-jgd.xml')
root = tree.getroot()

# Error handling for sqlite
try:
    # using "closing" is recommended
    # to avoid forgetting to close database
    with closing(sqlite3.connect(db_path)) as conn:
        c = conn.cursor()

        # Drop old table
        sql_drop = "DROP TABLE IF EXISTS stops"
        c.execute(sql_drop)

        # Create table
        sql_create = '''CREATE TABLE IF NOT EXISTS stops(
            id INT PRIMARY KEY,
            name TEXT,
            lat REAL,
            lon REAL)'''
        c.execute(sql_create)

        # When you want to identify a tag which includes namespace,
        # you must declare mapping of namespace to URL
        for stop in root.findall(".//jps:GM_Point", namespaces):

            # Extract GPS coordinate
            coord_str = stop.find(".//DirectPosition.coordinate")
            coord_arr = coord_str.text.split(' ')
            lat, lon = coord_arr[0], coord_arr[1]

            # Extract bus stop id: e.g. "n2210", and remove "n"
            stop_id_int = int(stop.attrib['id'].strip("n"))

            sql_insert = "INSERT INTO stops(id, lat, lon) VALUES(?, ?, ?)"
            c.execute(sql_insert, (stop_id_int, lat, lon))

        conn.commit()

        # When you want to identify a tag which includes namespace,
        # you must declare mapping of namespace to URL
        for stop in root.findall(".//ksj:ED01", namespaces):

            # Extract bus stop name
            stop_name = stop.find(".//ksj:BSN", namespaces).text

            # Extract bus stop id: e.g. "n2210", and remove "n"
            stop_id_str = stop.find(".//ksj:POS", namespaces).attrib['idref']
            stop_id_int = int(stop_id_str.strip("n"))

            sql_update = "UPDATE stops SET name = ? WHERE id = ?"
            c.execute(sql_update, (stop_name, stop_id_int))

        conn.commit()

        def show_database():
            """FOR TEST USE: check the content of the database"""
            c.execute("SELECT * FROM stops")
            print(c.fetchall())

        show_database()

except sqlite3.Error as e:
    print("Error occured in sqlite! :", e.args[0])

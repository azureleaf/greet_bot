import xml.etree.ElementTree as ET
import sqlite3
import constants
from contextlib import closing


def xml2sqlite():
    '''Extract bus stop data from the XML, and store in SQLite database
        Args: void
        Returns: void

        XML file was downloaded from MLIT (国土数値情報　バス停留所データ),
        which includes all the bus stop data in Miyagi prefecture as of 2010
    '''

    # Namespace mappings in the XML file
    namespaces = {
        "jps": "http://www.gsi.go.jp/GIS/jpgis/standardSchemas",
        "ksj": "http://nlftp.mlit.go.jp/ksj/schemas/ksj-app",
        "ksjc": "http://nlftp.mlit.go.jp/ksj/schemas/ksj-app-cd",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xlink": "http://www.w3.org/1999/xlink",
        "schemaLocation": "http://nlftp.mlit.go.jp/ksj/schemas/ksj-app \
        KsjAppSchema-P11.xsd",
    }

    tree = ET.parse(constants.BUS_POS_FILE_PATH)
    root = tree.getroot()

    # Error handling for sqlite
    try:
        # using "closing" is recommended
        # to avoid forgetting to close database
        with closing(sqlite3.connect(constants.DB_PATH)) as conn:
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

            # When you identify a XML tag which includes namespace,
            # (e.g. "jsp" is namespace in <jsp:books id="123"> tag),
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

            # When you use "find()" families on a tag which includes namespace,
            # you must declare mapping of namespace to URL
            for stop in root.findall(".//ksj:ED01", namespaces):

                # Extract bus stop name
                stop_name = stop.find(".//ksj:BSN", namespaces).text

                # Extract bus stop id (e.g. "n2210") and remove "n"
                stop_id_str = stop.find(
                    ".//ksj:POS", namespaces).attrib['idref']
                stop_id_int = int(stop_id_str.strip("n"))

                sql_update = "UPDATE stops SET name = ? WHERE id = ?"
                c.execute(sql_update, (stop_name, stop_id_int))

            conn.commit()

            def show_database():
                """FUNCTION FOR TEST USE
                Show the content of the database"""
                c.execute("SELECT * FROM stops")
                print(c.fetchall())

            show_database()

    except sqlite3.Error as e:
        print("Error in sqlite: ", e.args[0])


xml2sqlite()

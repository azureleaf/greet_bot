import xml.etree.ElementTree as ET
import os
import sqlite3

csv_path = os.getcwd() + '/bus_stops.csv'
db_path = os.getcwd() + '/busstop.db'
namespaces = {"jps": "http://www.gsi.go.jp/GIS/jpgis/standardSchemas"}

# tree = ET.parse('P11-10_04-jgd.xml')
tree = ET.parse('sample.xml')
root = tree.getroot()

with open(csv_path, mode="w") as f:
    # When you want to identify a tag which includes namespace,
    # you must declare mapping of namespace to URL
    for stop in root.findall(".//jps:GM_Point", namespaces):
        coord_str = stop.find(".//DirectPosition.coordinate")
        coord_arr = coord_str.text.split(' ')
        lat, lon = coord_arr[0], coord_arr[1]
        print(stop.attrib['id'], lat, lon)

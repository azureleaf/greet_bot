import xml.etree.ElementTree as ET
import os

csv_path = os.getcwd() + '/bus_stops.csv'


# tree = ET.parse('P11-10_04-jgd.xml')
tree = ET.parse('test.xml')
root = tree.getroot()

with open(csv_path, mode="w") as f:
    for stop in root.findall(".//DirectPosition.coordinate"):
        print(stop)

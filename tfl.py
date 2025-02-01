import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def fetch_stations_info():
    url = "https://tfl.gov.uk/tfl/syndication/feeds/cycle-hire/livecyclehireupdates.xml"
    response = requests.get(url)
    response.raise_for_status()  # Raise HTTPError if the request was not successful
    
    # Parse the XML
    root = ET.fromstring(response.content)
    
    stations_info = []
    for station in root.findall("station"):

        name = station.find("name").text
        terminal_name = station.find("terminalName").text
        lat = float(station.find("lat").text)
        lon = float(station.find("long").text)

        stations_info.append(
            (name, terminal_name, lat, lon))
    
    return stations_info
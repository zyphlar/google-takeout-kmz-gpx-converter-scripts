#!/usr/bin/env python3

import argparse
import json
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


def ingestJson(geoJsonFilepath):
    poiList = []
    with open(geoJsonFilepath, encoding='utf-8') as fileObj:
        data = json.load(fileObj)
        gmQuery = re.compile("http://maps.google.com/\\?q=([-0-9.]+),([-0-9.]+)")
        for f in data["features"]:
            title = f["properties"].get("location", {}).get("name", '')
            gmapsUrl = f["properties"].get("google_maps_url", '')
            lon = f["geometry"]["coordinates"][0]
            lat = f["geometry"]["coordinates"][1]
            cmt = f["properties"].get("Comment", '')
            link = f["properties"].get("google_maps_url", '')

            # Fill in blanks for Organic Maps
            if cmt == '':
                cmt = '<a href="'+link+'">'+link+'</a>'

            # Handle starred places without proper coordinates/comments
            if lat == 0 and lon == 0:
                if title == '':
                    title = "Starred Place"
                matches = gmQuery.findall(gmapsUrl)
                if len(matches) == 1 and len(matches[0]) == 2:
                    lat = matches[0][0] # Google order is backwards from GeoJSON
                    lon = matches[0][1]
                else:
                    # We have basically no information, so at least provide OM the link
                    cmt = '<a href="'+link+'">'+link+'</a>'

            poiList.append({'title': title,
                            'comment': cmt,
                            'date': f["properties"]["date"],
                            'lon': lon,
                            'lat': lat,
                            'link': link,
                            'address': f["properties"].get("location", {}).get("address", '')})
    return poiList


def dumpGpx(gpxFilePath, poiList):
    gpx = ET.Element("gpx", version="1.1", creator="", xmlns="http://www.topografix.com/GPX/1/1")
    for poi in poiList:
        wpt = ET.SubElement(gpx, "wpt", lat=str(poi["lat"]), lon=str(poi["lon"]))
        ET.SubElement(wpt, "name").text = poi["title"]
        ET.SubElement(wpt, "desc").text = poi["address"]
        ET.SubElement(wpt, "cmt").text = poi["comment"]
        ET.SubElement(wpt, "link").text = poi["link"]
        ET.SubElement(wpt, "time").text = poi["date"]
        ext = ET.SubElement(wpt, "extensions")
        ET.SubElement(ext, "color").text = "0000ff"
    xmlstr = minidom.parseString(ET.tostring(gpx)).toprettyxml(encoding="utf-8", indent="  ")
    with open(gpxFilePath, "wb") as f:
        f.write(xmlstr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputGeoJsonFilepath', required=True)
    parser.add_argument('--outputGpxFilepath', required=True)
    args = parser.parse_args()

    poiList = ingestJson(args.inputGeoJsonFilepath)
    dumpGpx(args.outputGpxFilepath, poiList=poiList)


if __name__ == "__main__":
    main()
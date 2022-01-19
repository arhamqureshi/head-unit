import subprocess
import xml.etree.ElementTree as ET
from gps import *
from g import getPositionData
from timeit import default_timer as timer

# https://wiki.openstreetmap.org/wiki/Overpass_API/Installation#Option_1:_Installation_via_tarball
# https://wiki.openstreetmap.org/wiki/User:Mmd/Overpass_API/Raspberry
# https://forum.openstreetmap.org/viewtopic.php?id=62085

def retrieve_speed_limit(lat, lon):
    query = "way[highway][name](around:7, {}, {});out;".format(lat, lon)
    result = subprocess.run(
        [
            "osm3s_query", 
            "--db-dir=/home/pi/OSM-DB"
        ], 
        input=query.encode(), 
        capture_output=True
    )

    tree = ET.ElementTree(ET.fromstring(result.stdout.decode('utf-8')))

    potential_speed_limits = []
    for way in tree.findall("way"):
        way_name_speed = {}
        for tag in way.findall("tag"):
            if tag.attrib['k'] == "name":
                way_name_speed['name'] = (tag.attrib['v'])
            if tag.attrib['k'] == "maxspeed":
                way_name_speed['speed'] = (tag.attrib['v'])
        if "name" in way_name_speed and "speed" not in way_name_speed:
            way_name_speed['speed'] = "(50)"

        if "name" in way_name_speed and "speed" in way_name_speed:
            potential_speed_limits.append(way_name_speed)
    
    if len(potential_speed_limits) > 0:
        return {
                "road": potential_speed_limits[0]['name'],
                "speed": potential_speed_limits[0]['speed']
            }
    
    return {"road": "Road Name Unknown", "speed": "--"}

if __name__ == "__main__":
    ## Basic Tests
    # lonlats = [
    #     ["Barry Drive", -35.27541978996088,149.12640978736866],
    #     ["Belconnen Way", -35.26004416030136, 149.10130045382633],
    #     ["Parkes Way", -35.285321851639615, 149.0923723969746],
    #     ["Athllon Dr", -35.373688726180035, 149.0930194577998],
    #     ["Johnson Dr", -35.43250819697518, 149.1009947749952],
    #     ["Mirrabei Dr", -35.175558927920555, 149.12213736699624]
    # ]
    # for ll in lonlats:
    #     print(retrieve_speed_limit(ll[1], ll[2]))

    gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
    start = timer()
    while True:
        end = timer()
        if (end - start) > 5:
            gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
            start = timer()
        lon_lat = getPositionData(gpsd)
        if lon_lat:
            if lon_lat['latitude'] != "Unknown":
                result = retrieve_speed_limit(lon_lat['latitude'], lon_lat['longitude'])
                result['active'] = True
                print(result)
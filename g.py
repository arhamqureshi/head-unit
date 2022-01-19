from gps import *
import time

def getPositionData(gps):
    nx = gps.next()
    # For a list of all supported classes and fields refer to:
    # https://gpsd.gitlab.io/gpsd/gpsd_json.html

    if nx['class'] == 'TPV':
        latitude = getattr(nx,'lat', "Unknown")
        longitude = getattr(nx,'lon', "Unknown")
        return {"longitude": str(longitude), "latitude": str(latitude)}
    return {"longitude": "Unknown", "latitude": "Unknown"}


if __name__ == "__main__":
    running = True
    gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

    try:
        prev = ""
        while running:
            cur = (getPositionData(gpsd))
            if cur['longitude'] != "Unknown":
                if str(cur) != prev:
                    prev = str(cur)
                    print(cur)

    except (KeyboardInterrupt):
        running = False
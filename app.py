#!/usr/bin/env python

# AUTHOR: Arham Qureshi (u6378881)

async_mode = 'threading'

import threading, webbrowser
from flask import Flask, render_template, request, Response
from flask_socketio import SocketIO, emit
from speed_limit import retrieve_speed_limit
from g import getPositionData
from gps import *
from camera_v4l2 import Camera
import obd, subprocess, time, os
from timeit import default_timer as timer


app = Flask(__name__)

socketio = SocketIO(app, async_mode=async_mode)
obd_thread = None
speed_thread = None
speed_limit_thread = None
stop_threads = False

res = None
ports = None
connection = None

def establish_obd_connection():

    global res
    global ports
    global connection 
    
    while res == None:
        ports = obd.scan_serial()
        connection = obd.OBD(portstr=ports[0], protocol="6", fast=False)

        cmd = obd.commands.RPM # select an OBD command (sensor)
        
        response = connection.query(cmd) # send the command, and parse the response

        res = response.value
        if res == None:
            connection.close()

def speed_background_thread():
    global res

    if res == None:
        establish_obd_connection()

    while True:
        global stop_threads
        if stop_threads:
            break

        speed_data = {"SPEED": 0}
        speed = obd.commands.SPEED # select an OBD command (sensor)
        response = connection.query(speed) # send the command, and parse the response
        speed_data['SPEED'] = str(response.value).split(" ")[0]
        
        # res = response.value
        socketio.emit(
            'speed_data',
            speed_data,
            namespace='/sensor'
        )
        

def obd_background_thread():
    global res

    if res == None:
        establish_obd_connection()

    while True:
        global stop_threads
        if stop_threads:
            break

        obd_data = {"RPM": 0}
        rpm = obd.commands.RPM # select an OBD command (sensor)
        response = connection.query(rpm) # send the command, and parse the response
        obd_data['RPM'] = float(str(response.value).split(" ")[0])
        
        commands = ['COOLANT_TEMP', 'INTAKE_TEMP', 'ABSOLUTE_LOAD', 'RELATIVE_THROTTLE_POS']

        for command in commands:
            if connection.supports(obd.commands[command]):
                obd_data[command] = "{:.1f}".format(float(str(connection.query(obd.commands[command]).value).split(" ")[0]))
        
        c = connection.query(obd.commands['STATUS']).value
        obd_data['MIL'] = c.MIL
        obd_data["DTC_Count"] = c.DTC_count

        errors = connection.query(obd.commands['GET_DTC']).value
        
        # Dummy Data
        # errors = [
        #     ("P0104", "Mass or Volume Air Flow Circuit Intermittent"),
        #     ("B0003", ""),
        #     ("C0123", "")
        # ]
        
        obd_data["DTC_Count"] = len(errors)
        obd_data["DTC_Errors"] = errors

        socketio.emit(
            'obd_data',
            obd_data,
            namespace='/sensor'
        )


def speed_limit_background_thread():
    gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
    start = timer()
    while True:
        global stop_threads
        if stop_threads:
            break

        end = timer()
        if (end - start) > 5:
            gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
            start = timer()

        lon_lat = getPositionData(gpsd)
        if lon_lat:
            if lon_lat['latitude'] != "Unknown":
                result = retrieve_speed_limit(lon_lat['latitude'], lon_lat['longitude'])
                result['active'] = True

                socketio.emit(
                    'speed_limit',
                    result,
                    namespace='/sensor'
                )
            else:
                socketio.emit(
                    'speed_limit',
                    {"active": False},
                    namespace='/sensor'
                )
        else:
            socketio.emit(
                'speed_limit',
                {"active": False, "msg": "Searching for GPS"},
                namespace='/sensor'
            )

def reset_threads():
    global stop_threads
    stop_threads = True
    time.sleep(0.5)
    stop_threads = False

    global speed_limit_thread
    speed_limit_thread = None

    global obd_thread
    obd_thread = None

    global speed_thread
    speed_thread = None

    # global res
    # global ports
    # global connection
    # res = None
    # ports = None
    # connection = None

@app.route('/')
def index():
    reset_threads()

    global speed_limit_thread
    if speed_limit_thread is None:
        speed_limit_thread = socketio.start_background_task(target=speed_limit_background_thread)

    global speed_thread
    if speed_thread is None:
        speed_thread = socketio.start_background_task(target=speed_background_thread)

    return render_template('index.html')

@app.route("/command", methods=["POST"])
def command():
    command = request.form['command']
    
    if command == "poweroff":
        subprocess.Popen("sudo shutdown -h now", shell=True)

    if command == "reboot":
        subprocess.Popen("sudo reboot", shell=True)
        
    return {"result": None}

@app.route('/reverse_camera')
def reverse_camera():
    reset_threads()
    return render_template('reverse_camera.html')

@app.route('/diagnostics')
def diagnostics():
    reset_threads()

    global obd_thread
    if obd_thread is None:
        obd_thread = socketio.start_background_task(target=obd_background_thread)

    return render_template('diagnostics.html')

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@socketio.on('connect', namespace='/sensor')
def test_connect():
    emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/sensor')
def test_disconnect():
    print('Client disconnected', request.sid)

def open_browser():
    cmd = "/usr/bin/chromium-browser --start-fullscreen --app=http://127.0.0.1:8081"
    os.system(cmd)

if __name__ == '__main__':
    connect_obd = subprocess.Popen("sudo /usr/bin/rfcomm bind hci0 00:1D:A5:01:E1:FB", shell=True)
    connect_obd.wait()

    threading.Timer(5, lambda: open_browser()).start()    

    socketio.run(app, port=8081, use_reloader=False)

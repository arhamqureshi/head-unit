import obd, subprocess

def retrieve_obd_data():
    res = None
    ports = None
    connection = None

    while res == None:
        # OBD setup
        # obd.logger.setLevel(obd.logging.DEBUG)
        try:
            a1 = subprocess.Popen("sudo /usr/bin/rfcomm unbind hci0", shell=True)
            a1.wait()
            a2 = subprocess.Popen("sudo /usr/bin/rfcomm bind hci0 00:1D:A5:01:E1:FB", shell=True)
            a2.wait()
        except:
            pass
        ports = obd.scan_serial()

        connection = obd.OBD(portstr=ports[0], protocol="6", fast=False)

        # while True:
        cmd = obd.commands.RPM # select an OBD command (sensor)
        
        response = connection.query(cmd) # send the command, and parse the response

        res = response.value
        if res == None:
            connection.close()


    while True:
        data = {"SPEED": 0, "RPM": 0}
        rpm = obd.commands.RPM # select an OBD command (sensor)
        response = connection.query(rpm) # send the command, and parse the response
        data['RPM'] = float(str(response.value).split(" ")[0])
        
        res = response.value

        commands = ['SPEED', 'COOLANT_TEMP', 'INTAKE_TEMP', 'ABSOLUTE_LOAD', 'RELATIVE_THROTTLE_POS']

        for command in commands:
            if connection.supports(obd.commands[command]):
                data[command] = "{:.1f}".format(float(str(connection.query(obd.commands[command]).value).split(" ")[0]))
        
        c = connection.query(obd.commands['STATUS']).value
        data['MIL'] = c.MIL

        errors = connection.query(obd.commands['GET_DTC']).value
        # errors = [
        #     ("P0104", "Mass or Volume Air Flow Circuit Intermittent"),
        #     ("B0003", ""),
        #     ("C0123", "")
        # ]
        
        data["DTC_Count"] = len(errors)
        data["DTC_Errors"] = errors
        print(data)
        return None

if __name__ == "__main__":
    retrieve_obd_data()




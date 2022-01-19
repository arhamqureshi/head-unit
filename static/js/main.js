/* AUTHOR: Arham Qureshi (u6378881) */

var SPEED_LIMIT = "--";

function set_theme() {
    let theme = localStorage.getItem("THEME")

    if (theme === "dark") {
        $("body").css("background-color", "#121212")
        $("body").css("color", "white")
        $(".menu-item").css("background-color", "#181818")
        $(".modal-content").css("background-color", "#2b2b2b")
    } else {
        $("body").css("background-color", "white")
        $("body").css("color", "black")
        $(".menu-item").css("background-color", "#e8e8e8")
    }
}

function send_command(command) {
    $.post("/command", {
        command: command
    });
}

function toggle_theme() {
    let current_theme = localStorage.getItem("THEME")

    if (current_theme === "dark") {
        localStorage.setItem('THEME', "light");
    } else {
        localStorage.setItem('THEME', "dark");
    }

    set_theme()
}


$(document).ready(function () {
    namespace = '/sensor';
    set_theme()
    var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);

    socket.on('speed_limit', function (msg) {
        if (msg['active']) {
            $("#road").html(msg["road"])
            $("#speed").html(msg["speed"])
            SPEED_LIMIT = parseInt(msg["speed"].replace("(", "").replace(")",""))
        } else {
            if ("msg" in msg) {
                $("#road").html(msg["msg"])
                $("#speed").html("Searching..")
            }
            SPEED_LIMIT = "--"
        }
    });

    socket.on('speed_data', function (msg) {
        if ("SPEED" in msg) {
            let speed = parseInt(msg["SPEED"].split(".")[0])
            $("#obd_speed").html(speed)
            if (SPEED_LIMIT !== "--") {
                if (speed > SPEED_LIMIT) {
                    $("body").css("background-color", "#bb2d2d")
                    $("body").css("color", "white")
                    $(".menu-item").css("background-color", "#902626")
                } else {
                   set_theme()
                }
            }
        }
    });

    socket.on('obd_data', function (msg) {
        if ("RPM" in msg) {
            $("#RPM").html(msg["RPM"])
            $("#COOLANT_TEMP").html(msg["COOLANT_TEMP"] + "c")
            $("#INTAKE_TEMP").html(msg["INTAKE_TEMP"] + "c")
            $("#ABSOLUTE_LOAD").html(msg["ABSOLUTE_LOAD"] + "%")
            $("#RELATIVE_THROTTLE_POS").html(msg["RELATIVE_THROTTLE_POS"] + "%")

            if (msg["MIL"]) {
                $("#MIL").html("CHECK ENGINE")
                $("#MIL").css('color', 'darkred')
            } else {
                $("#MIL").html("GOOD")
                $("#MIL").css('color', 'darkgreen')
            }

            $("#DTC_Count").html(msg["DTC_Count"])
            if (msg["DTC_Count"] === 0) {
                $("#DTC_Count").css("color", "darkgreen")
            } else {
                $("#DTC_Count").css("color", "darkred")
                $("#dtc-errors").empty();

                let title = document.createElement('span')
                title.innerHTML = "Errors Found"
                title.style.fontWeight = "bold"
                $("#dtc-errors").append(title)

                msg['DTC_Errors'].forEach(element => {


                    let p = document.createElement('p')
                    let code = element[0]
                    let message = element[1]
                    if (element[1] === "") {
                        message = "Unknown Code. Check car manual."
                    }

                    p.innerHTML = code + " - " + message;

                    $("#dtc-errors").append(p)
                });
            }

        }
    });

    // event handler for new connections
    socket.on('connect', function () {
        socket.emit('my event', { data: 'I\'m connected!' });
    });
});
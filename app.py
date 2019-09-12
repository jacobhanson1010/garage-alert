import os
import threading
from time import localtime, strftime

import requests
from flask import Flask, request, make_response

app = Flask(__name__)
alert_timer = None
time_opened = None
starting_timer_length = int(os.environ.get('TIMER', 10 * 60))
current_timer_length = None


def start_alert_timer(timer_length):
    global alert_timer
    global current_timer_length
    current_timer_length = timer_length

    if alert_timer is not None:
        # this shouldn't happen, the same garage door opening twice?
        cancel_alert_timer()

    alert_timer = threading.Timer(timer_length, send_alert)
    alert_timer.start()
    print('alert_timer scheduled for ' + str(current_timer_length) + ' from now')


def cancel_alert_timer():
    global alert_timer

    if alert_timer is not None:
        alert_timer.cancel()


def send_alert():
    global time_opened
    global current_timer_length

    # send the alert
    print('sending alert')
    print(requests.get(str(os.environ.get('ALERT_URL', None)),
                       {'value1': strftime("%I:%M %p", time_opened)}))

    # schedule another timer
    start_alert_timer(current_timer_length * 2)

    return


def auth(auth):
    return auth == str(os.environ.get('TOKEN', 'token'))


@app.route('/garage-opened', methods=['POST'])
def garage_opened():
    global time_opened
    global current_timer_length

    if not auth(request.json['auth']):
        return '', 401

    time_opened = localtime()
    start_alert_timer(starting_timer_length)
    print('garage door opened, alert timer scheduled')
    return 'alert timer scheduled'


@app.route('/garage-closed', methods=['POST'])
def garage_closed():
    if not auth(request.json['auth']):
        return '', 401

    cancel_alert_timer()
    print('garage door closed, alert timer cancelled')
    return 'alert timer cancelled'


if __name__ == '__main__':
    app.run()

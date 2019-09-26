import multiprocessing
import os
import threading

import pendulum as pendulum
import requests
from flask import Flask, request, make_response

print('number of cpus ' + str(multiprocessing.cpu_count()))
app = Flask(__name__)
alert_timer = None
time_opened = None
starting_timer_length = int(os.environ.get('TIMER', 600))
token = str(os.environ.get('TOKEN', None))
alert_url = str(os.environ.get('ALERT_URL', None))
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
    print(requests.get(alert_url,
                       {'value1': time_opened.format('h:mm:ss A')}))

    # schedule another timer
    start_alert_timer(current_timer_length * 2)

    return


def auth(tok):
    global token
    return tok == token


@app.route('/garage-opened', methods=['POST'])
def garage_opened():
    global time_opened
    global current_timer_length

    if not auth(request.json['auth']):
        return '', 401

    time_opened = pendulum.now('America/Chicago')
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


@app.route('/', methods=['POST'])
def dummy():
    global token
    global alert_url
    global starting_timer_length
    print('token ' + token)
    print('alert_url ' + alert_url)
    print('starting_timer_length ' + str(starting_timer_length))
    return 'hello world'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

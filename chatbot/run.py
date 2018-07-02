#!/usr/bin/python3
#
# File: run.py
# The main chatbot
# Copyright 2018
# The Gerrit Group
#
# (Test) usage
# ~ python3 run.py

# Imports
import eventlet
eventlet.monkey_patch(socket=True)
from flask import Flask, render_template, request
from flask_socketio import SocketIO
import logging
import os

from main_algorithm import Main
from threading import Thread

# Standard settings
template_dir = ('interface')
app = Flask(__name__, template_folder=template_dir, static_folder=template_dir)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app,  async_handlers=True,
                    async_mode="threading", manage_session=False)

# Store visiting clients together with their main class instance
clients = {}


@app.route('/')
def index():
    """
        Init template after connection
    """
    return render_template('bot.html')


@socketio.on('connect')
def connect():
    """
        Connect to dictionary
    """
    print("NEW CONNECTION")
    print("IP: %s " % (request.remote_addr)+request.sid)


@socketio.on('query')
def q(input):
    """
        Say to correct bot which input is given
        Input:
            input: str (cleaned by jQuery -> get_input() does it by Python)
    """
    bot = clients[request.sid]
    bot[0].get_chatbot().get_input(input)


@socketio.on('language')
def l(lang):
    """
        Change the language of the chatbot
        Input:
            language: lang
    """
    bot = clients[request.sid][0]
    C = bot.get_chatbot()
    V = bot.get_conversation()
    if lang == 1:
        C.set_language((lang, 'English'))
        V.set_main_language((lang, 'English'))
    else:
        C.set_language((lang, 'Dutch'))
        C.set_main_language((lang, 'Dutch'))
    C.user_set_language()


@socketio.on('hackerman')
def h():
    """
        Someone is trying to put html or something to gerrit
    """
    bot = clients[request.sid]
    bot[0].get_chatbot().fool()


@socketio.on('start')
def start(methods=['POST']):
    """
        Start program on connection
        Assign each client a unique session ID and link it to a main instance
    """
    print("%s Started" % (request.sid))
    # Disable Logs
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    # Start new chatbot conversation
    bot = Main(socketio, request.sid)
    t = Thread(target=bot.run, name=request.sid)
    clients[request.sid] = (bot, t)
    t.start()


@socketio.on('disconnected')
def disconnect():
    """
        Remove connection from dictionary
    """
    print("%s Disconnected " % (request.sid) + request.remote_addr)
    try:
        bot = clients[request.sid]
        bot[0].get_chatbot().check_log()
        bot[1].join()
        if is_alive(bot[1]):
            print("Tim stop")
        else:
            print("bram boterham")
        clients = clients.pop(request.sid, None)
    except:
        print("Failed to stop", request.sid)


if __name__ == '__main__':
    # Host to local port
    socketio.run(app, host='0.0.0.0', debug=True)

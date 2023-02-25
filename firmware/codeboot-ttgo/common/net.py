import config
import ttgo as dev

import usocketio.client
from utime import time

import network

__all__ = ["NetError", "get_id", "get_network_id", "push_handler", "pop_handler", "get_handler",
           "set_handler", "set_trace", "connect", "disconnect", "send", "broadcast", "peers", "set_wifi"]

PEERS_SCAN_INTERVAL = 5

_connection = None
_trace = False
_network_id = None
_handlers_stack = []
_emit_queue = []
_peers = []

def _reset():
    global _connection
    global _trace
    global _network_id

    if _connection: _connection.close()

    _connection = None

    _trace = False
    _network_id = None
    _handlers_stack.clear()
    _emit_queue.clear()
    _peers.clear()

# API

class NetError(Exception):
    pass

def set_wifi(ssid, pwd):
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(ssid, pwd)

def get_id(timeout=None):
    return config.device_id

def get_network_id():
    return _network_id

def push_handler(handler):
    _handlers_stack.append(handler)

def pop_handler():
    if len(_handlers_stack) <= 1:
        raise IndexError("cannot pop the only remaining handler")

    return _handlers_stack.pop()

def get_handler():
    return _handlers_stack[-1]

def set_handler(handler):
    _handlers_stack[-1] = handler

def set_trace(x):
    global _trace
    _trace = bool(x)

def connect(network_id, handler):
    # reset previous connection
    _reset()

    # Fetch id
    id = get_id()

    def attempt_connect():
        try:
            socket = usocketio.client.connect(config.network_url, "username=" + id)
        except OSError:
            print("could not connect...")
            return

        print("Connection success!")
        return success(socket)

    def success(socket):
        global _connection
        global _network_id

        # Setup current handler
        push_handler(handler)

        _connection = socket
        _network_id = network_id

        # Join the 'network'
        socket.emit("join_room", network_id)

        def beat():
            socket.emit("heartbeat", "")
            dev.after(5, beat)

        beat()

        @socket.on("heartbeat")
        @socket.on("join_room")
        def add_peer(data):
            username = data[0]
            if username != get_id() and username not in _peers:
                _peers.append(username)

        @socket.on("leave_room")
        def remove_peer(data):
            username = data[0]
            if username in _peers:
                _peers.remove(username)

        # Setup listeners, we listen to our own id and to "*" which means 'everybody'
        @socket.on(id)
        @socket.on("*")
        def handler_wrapper(data):
            # Ignore room since net allows connection to a single room
            username, _, message = data
            i = len(_handlers_stack)
            while i > 0:
                i -= 1
                if not _handlers_stack[i](username, message):
                    i = 0 # stop bubbling

        # Clean up event after disconnect
        @socket.on("disconnect")
        def after_disconnect(*args):
            _reset()

        # Now that we have a connection, emit queued events
        for to, data in _emit_queue:
            send(to, data)

        _emit_queue.clear()
    
    attempt_connect()

def disconnect():
    if _connection:
        _connection.close()

def send(to, data):
    if _connection:
        # Active connection, emit event
        _connection.emit(to, data)
    else:
        # Awaiting connection with network, queue event to be emitted later
        _emit_queue.append((to, data))

def broadcast(data):
    send("*", data)

def peers():
    return _peers.copy() if _connection else []

# Add id and network_id as module properties
__properties__ = {
    'id': get_id,
    'network_id': get_network_id,
    'connected': lambda: False if not _connection else _connection.connected
}

def __getattr__(name):
    try:
        return __properties__[name]()
    except KeyError:
        raise AttributeError("module '" + __name__ + "' has no attribute '" + name + "'")

def __dir__():
    return __all__ + list(__properties__)


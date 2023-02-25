from codeboot _codeboot import readFile
from _ffi import host_eval
from js import setTimeout

import socketio
from time import time



import network

def set_wifi(ssid, pwd):
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(ssid, pwd)


PEERS_SCAN_INTERVAL = 5

_connection = None
_trace = False
_handlers_stack = []
_emit_queue = []
_peers = []

def _reset():
    global _connection
    global _trace

    if _connection: _connection.disconnect()

    _connection = None
    _trace = False
    _handlers_stack.clear()
    _emit_queue.clear()
    _peers.clear()

def _start_peers_scan():

    def scan():
        if _connection:
            _connection.emit("scan_room", get_network_id(), callback=_update_peers)

        dev.after(PEERS_SCAN_INTERVAL, scan)

    scan()

def _update_peers(peers):

    # remove own id from list
    try:
        peers.remove(get_id())
    except ValueError:
        pass

    _peers[:] = peers

def _wrapped_logger(updown="-"):

    def _logger(event, data):
        event = repr(event)
        padded_event = event + " " * (12 - len(event)) # chosen to align with 'leave_room'
        print("NET " + updown, padded_event, "|", "data:", repr(data))

    def logger_wrapper(*args):
        if not _trace:
            return

        try:
            _logger(*args)
        except Exception as e:
            print("NET " + updown, "exception in trace:", type(e).__name__ + ":", e)

    return logger_wrapper

_up_logger = _wrapped_logger("^")
_down_logger = _wrapped_logger("v")

# API

class NetError(Exception):
    pass

def get_id(timeout=None):
    return config.id

def get_network_id():
    return host_eval("rte.vm.net.getNetworkId()")

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

    # Request connection
    socket = socketio.Client(..., "username=" + id)

    # Setup current handler
    push_handler(handler)

    def after_connection(*args):
        global _connection

        _connection = socket

        # Join the 'network'
        socket.emit("join_room", network_id, callback=_update_peers)

        def handler_wrapper(data):
            # Ignore room since net allows connection to a single room
            username, _, message = data
            i = len(_handlers_stack)
            while i > 0:
                i -= 1
                if not _handlers_stack[i](username, message):
                    i = 0 # stop bubbling

        # Setup listeners, we listen to our own id and to "*" which means 'everybody'
        socket.on(id, handler_wrapper)
        socket.on("*", handler_wrapper)

        # Listen to all events for logging
        socket.prependAny(_down_logger)

        # Clean up event after disconnect
        def after_disconnect(*args):
            _reset()

        socket.once("disconnect", after_disconnect)

        # Now that we have a connection, emit queued events
        for to, data in _emit_queue:
            send(to, data)

        _emit_queue.clear()

    socket.once("connect", after_connection)

def disconnect():
    if _connection:
        _connection.disconnect()

def send(to, data):
    if _connection:
        # Active connection, emit event
        _connection.emit(to, data)
        _up_logger(to, data)
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
    'network_id': get_network_id
}

def __getattr__(name):
    try:
        return __properties__[name]()
    except KeyError:
        raise AttributeError("module '" + __name__ + "' has no attribute '" + name + "'")

def __dir__():
    return __all__ + list(__properties__)

_start_peers_scan()

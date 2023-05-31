import _config

connected = False

# API

class NetError(Exception):
    pass

def set_wifi(ssid, pwd):
    pass  # this does nothing on codeBoot

def get_id(timeout=None):
    return _config.id

def get_network_id():
    return None

def push_handler(handler):
    pass

def pop_handler():
    pass

def get_handler():
    return None

def set_handler(handler):
    return None

def set_trace(x):
    pass

def connect(network_id, handler):
    pass

def disconnect():
    pass

def send(to, data):
    pass

def broadcast(data):
    pass

def peers():
    return []

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

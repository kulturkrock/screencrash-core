
from .client import Client

import json


_START = b'\x00'
_STOP = b'\xFF'


def valid_channel(x):
    return isinstance(x, int) and x >= 0


class Message:

    def __init__(self, values: dict = None, sender: Client = None):
        self.values = values or dict()
        self.sender = sender

    def __getattr__(self, item):
        return self.values[item]

    def __setattr__(self, key, value):
        if key == 'channel' and not valid_channel(value):
            raise Exception("Invalid channel value: " + repr(value))
        self.values[key] = value

    @classmethod
    def from_bytes(cls, data, sender: Client = None):
        if len(data) < 4:
            raise Exception("Message data too short")
        elif data[0] != _START:
            raise Exception("Message data missing start byte")
        elif data[-1] != _STOP:
            raise Exception("Message data missing stop byte")
        obj = json.loads(data[1:-1], encoding='utf-8')
        if not valid_channel(obj.get('channel', None)):
            raise Exception("Message data has invalid channel number")
        return Message(obj, sender)

    def to_bytes(self):
        if not valid_channel(self.channel):
            raise Exception("Message has no valid channel number set")
        return _START + json.dumps(self.values).encode('utf-8') + _STOP

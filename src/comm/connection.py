
import logging

from .message import Message


class ConnectionBase:

    def __init__(self):
        self.client = None
        self._receive_buffer = bytearray()

    def on_message(self, msg: Message):
        logging.debug("Received message " + repr(msg))

    def accept_data(self, data: bytes or bytearray):
        self._receive_buffer += bytearray(data)
        while len(self._receive_buffer) > 0:
            idx = self._receive_buffer.find(0x00)
            if idx < 0:
                idx = len(self._receive_buffer)
            if idx != 0:
                logging.warning('Connection discarding {} bytes of data', idx)
                self._receive_buffer = self._receive_buffer[idx:]
            if idx > 0:
                msg_bytes = self._receive_buffer[:idx+1]
                self._receive_buffer = self._receive_buffer[idx+1:]
                try:
                    msg = Message.from_bytes(msg_bytes, self.client)
                except Exception as err:
                    logging.error('Failed to convert bytes to message: ' + str(err))
                    continue
                self.on_message(msg)
            else:
                break

    def send_message(self, msg: Message):
        raise NotImplementedError("Connection has not implemented send_message")

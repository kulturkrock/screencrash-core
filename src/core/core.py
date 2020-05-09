
import logging

from comm import client
from comm.message import Message
from .opus import Opus


class Core:

    def __init__(self):
        self.opus = Opus()

    def broadcast(self, msg: Message, exclude: client = None):
        raise NotImplementedError()  # TODO: Handle broadcasting

    def process_message(self, sender: client, msg: Message):
        if not isinstance(msg, Message):
            logging.error('Cannot process message of incorrect type: ' + repr(msg))
            return
        channel_number = msg['channel']
        if not isinstance(channel_number, int) or channel_number < 0:
            logging.error('Message lacking valid channel number: ' + repr(msg))
            return
        elif channel_number == 0:
            self.broadcast(msg, exclude=sender)
        elif channel_number == 3:
            if sender.isComponent:
                logging.warning(f'Rejecting incoming message on channel {channel_number} from Component: {repr(msg)}')
            else:
                pass  # TODO: Handle UI commands
        elif channel_number == 4:
            pass  # TODO: Handle Opus commands
        elif channel_number < 10:
            logging.warning(f'Rejecting incoming message on channel {channel_number}: {repr(msg)}')
        else:
            pass  # TODO: Handle user/Opus commands

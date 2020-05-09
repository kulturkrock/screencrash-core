
import zmq
import zmq.asyncio

from .client import Client
from .connection import ConnectionBase
from .message import Message


class ZmqConnection(ConnectionBase):

    def __init__(self, socket):
        super().__init__()
        self.socket = socket

    def send_message(self, msg: Message):
        pass


class ZmqServer:

    def __init__(self, host='localhost', port=8002, schema='tcp'):
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.bind(f'{schema}://{host}:{port}')
        self.clients = set()

    def _register(self, client: Client):
        self.clients.add(client)

    def _unregister(self, client: Client):
        self.clients.remove(client)

    async def _handler(self, socket):
        conn = ZmqConnection(socket)
        client = Client(conn)
        self._register(client)
        try:
            while True:
                frame = await socket.recv()
                if isinstance(frame, bytes):
                    conn.accept_data(frame)
                else:
                    raise Exception("Invalid data frame?")  # FIXME: ?
        finally:
            self._unregister(client)


import websockets

from .client import Client
from .connection import ConnectionBase
from .message import Message


class WebsocketConnection(ConnectionBase):

    def __init__(self, socket: websockets.WebSocketServerProtocol):
        super().__init__()
        self.socket = socket

    def send_message(self, msg: Message):
        self.socket.send(msg.to_bytes())


class WebsocketServer:

    def __init__(self, host='localhost', port=8001):
        self.server = websockets.serve(self._handler, host, port)
        self.clients = set()

    def _register(self, client: Client):
        self.clients.add(client)

    def _unregister(self, client: Client):
        self.clients.remove(client)

    async def _handler(self, socket: websockets.WebSocketServerProtocol, path: str):
        conn = WebsocketConnection(socket)
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

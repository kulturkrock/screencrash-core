
import websockets

from .client import Client
from .connection import ConnectionBase
from .message import Message


class WebsocketClient(Client):

    def __init__(self):
        super().__init__()


class WebsocketConnection(ConnectionBase):

    def __init__(self, socket: websockets.WebSocketServerProtocol, client: WebsocketClient):
        super().__init__(client)
        self.socket = socket

    def send_message(self, msg: Message):
        self.socket.send(msg.to_bytes())


class WebsocketServer:

    def __init__(self, host='localhost', port=8001):
        self.server = websockets.serve(self._handler, host, port)
        self.clients = set()

    def _register(self, client: WebsocketClient):
        self.clients.add(client)

    def _unregister(self, client: WebsocketClient):
        self.clients.remove(client)

    async def _handler(self, socket: websockets.WebSocketServerProtocol, path: str):
        client = WebsocketClient()
        conn = WebsocketConnection(socket, client)
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

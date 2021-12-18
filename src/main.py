import asyncio
import json
from pathlib import Path
import websockets
from websockets.server import WebSocketServerProtocol

from opus import load_opus
from performance import Performance
from peers.ui import UI


class Core:
    """
    This is the main class, keeping track of all state.

    Parameters
    ----------
    port
        The port to run a websocket server on.
    """

    def __init__(self, port: int):
        self._port = port

    async def main(self):
        """The main loop."""
        self._opus = await load_opus(Path("resources") / "dev_opus.yaml")
        self._performance = Performance(self._opus)
        self._ui = UI(self._opus, self._performance.history)
        self._ui.add_event_listener("next-node", self.handle_next_node)
        async with websockets.serve(self.socket_listener, "localhost", self._port):
            await asyncio.Future()  # run forever

    async def socket_listener(self, websocket: WebSocketServerProtocol):
        # Wait for a hello
        message = await websocket.recv()
        message_dict = json.loads(message)
        client_type = message_dict["client"]
        if client_type == "ui":
            await self._ui.handle_socket(websocket)

    def handle_next_node(self):
        """Handle the UI going to the next node."""
        self._performance.next_node()
        self._ui.change_history(self._performance.history)


if __name__ == "__main__":
    core = Core(8001)
    try:
        asyncio.run(core.main())
    except KeyboardInterrupt:
        print('Exiting')

import asyncio
import json
from pathlib import Path
import websockets
from websockets.server import WebSocketServerProtocol

from opus import load_opus
from performance import Performance
from peers.internal import InternalPeer
from peers.screen import Screen
from peers.ui import UI


class Core:
    """
    This is the main class, keeping track of all state.

    Parameters
    ----------
    port
        The port to run a websocket server on
    """

    def __init__(self, port: int):
        self._port = port

    async def main(self):
        """The main loop."""
        self._opus = await load_opus(Path("resources") / "dev_opus.yaml")
        self._performance = Performance(self._opus)
        self._ui = UI(self._opus, self._performance.history)
        self._components = [InternalPeer()]

        self._ui.add_event_listener("next-node", self._performance.next_node)
        self._performance.add_event_listener(
            "history-changed", self._ui.changed_history)
        self._performance.add_event_listener("run-action", self._run_action)

        async with websockets.serve(self.socket_listener, "localhost", self._port):
            await asyncio.Future()  # run forever
    
    def _run_action(self, action_id):
        action = self._opus.action_templates.get(action_id)
        if action is None:
            print("Failed to find action with id {}. Skipping.".format(action_id))
            return
        assets = [self._opus.assets[key] for key in action.assets]
        handled = False
        for peer in self._components:
            if peer.handles_target(action.target):
                peer.handle_action(action.target, action.cmd, assets, action.params)
                handled = True
        if not handled:
            print("Warning: Action {} not handled by anyone ({})".format(action_id, action.target))

    async def socket_listener(self, websocket: WebSocketServerProtocol):
        """
        This function handles an incoming websocket connection.

        Parameters
        ----------
        websocket
            The websocket
        """
        # Wait for a hello
        message = await websocket.recv()
        message_dict = json.loads(message)
        client_type = message_dict["client"]
        if client_type == "ui":
            await self._ui.handle_socket(websocket)
        elif client_type == "screen":
            print("Adding screen component")
            new_peer = Screen()
            self._components.append(new_peer)
            await new_peer.handle_socket(websocket)


if __name__ == "__main__":
    core = Core(8001)
    try:
        asyncio.run(core.main())
    except KeyboardInterrupt:
        print('Exiting')

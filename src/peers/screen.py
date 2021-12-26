import json
from typing import List, Dict
from opus import Asset
import websockets
from websockets.server import WebSocketServerProtocol

from peers.component import ComponentPeer


class Screen(ComponentPeer):
    """
    Handles communication with screens.

    This has a websocket server that screens can connect to.

    Parameters
    ----------
    """

    def __init__(self):
        super().__init__(["image", "video"])
        self._websockets: List[WebSocketServerProtocol] = []
        self._current_entity_id = 1

    async def handle_socket(self, websocket: WebSocketServerProtocol):
        """This handles one websocket connection."""
        self._websockets.append(websocket)
        # Handle messages from the client
        async for message in websocket:
            message_dict = json.loads(message)
            message_type = message_dict["messageType"]
            if message_type == "heartbeat":
                pass  # Ignore heartbeats for now
            else:
                print(f"WARNING: Unknown message type {message_type}")
        # Websocket is closed
        self._websockets.remove(websocket)

    def handle_action(self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, str]):
        """Process the given action."""
        if cmd == "start":
            self.play_effect(target_type, assets[0], params.get("autostart", True))
        else:
            super().handle_action(target_type, cmd, assets, params)

    def play_effect(self, target_type: str, asset: Asset, autostart=True):
        websockets.broadcast(self._websockets, json.dumps({
            "command": "create",
            "entity_id": self._current_entity_id,
            "channel": 1,
            "type": target_type,
            "resource": asset.path
        }))
        websockets.broadcast(self._websockets, json.dumps(
            {"command": "show", "entity_id": self._current_entity_id, "channel": 1}
        ))
        if autostart:
            websockets.broadcast(self._websockets, json.dumps(
                {"command": "play", "entity_id": self._current_entity_id, "channel": 1}
            ))
        self._current_entity_id += 1
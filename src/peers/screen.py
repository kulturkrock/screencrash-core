import json
from typing import List, Dict
import websockets
from websockets.server import WebSocketServerProtocol

from opus import Effect, Opus
from util.event_emitter import EventEmitter


class Screen(EventEmitter):
    """
    Handles communication with screens.

    This has a websocket server that screens can connect to.

    Parameters
    ----------
    effects
        The effects that are relevant to the screen
    """

    def __init__(self, effects: Dict[str, Effect]):
        self._effects = effects
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

    def play_effect(self, name):
        websockets.broadcast(self._websockets, json.dumps({
            "command": "create",
            "entity_id": self._current_entity_id,
            "channel": 1,
            "type": self._effects[name].type,
            "resource": f"file://{str(self._effects[name].file)}"
        }))
        websockets.broadcast(self._websockets, json.dumps(
            {"command": "show", "entity_id": self._current_entity_id, "channel": 1}
        ))
        websockets.broadcast(self._websockets, json.dumps(
            {"command": "play", "entity_id": self._current_entity_id, "channel": 1}
        ))
        self._current_entity_id += 1

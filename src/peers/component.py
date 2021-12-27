import json
from typing import List, Dict
from opus import Asset
from util.event_emitter import EventEmitter

from websockets.server import WebSocketServerProtocol


class ComponentPeer(EventEmitter):
    """
    Base class for peers which accepts actions.

    Parameters
    ----------
    target_types
        Target types this peer listens too (e.g. audio, video, image etc.)
    """

    def __init__(self, target_types: List[str]):
        self._target_types = target_types
        self._websockets: List[WebSocketServerProtocol] = []

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

    def nof_instances(self):
        return len(self._websockets)

    def handles_target(self, target_type: str):
        """Checks whether this instance can handle actions of the given type."""
        return target_type in self._target_types

    def handle_action(self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, str]):
        """Process the given action."""
        print(f"Command not handled by subclass: {target_type}:{cmd}")
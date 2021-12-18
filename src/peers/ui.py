import asyncio
import base64
from dataclasses import asdict
import json
from typing import Callable, Dict, List, Optional
import websockets
from websockets.server import WebSocketServerProtocol

from opus import Opus

UIEventListener = Callable[[], None]


class UI:
    """
    Handles communication with UIs.

    This has a websocket server that the UI can connect to.

    Parameters
    ----------
    opus
        The opus. Some contents are sent in the initial handshake with a client.
    initial_history
        The initial history
    """

    def __init__(self, opus: Opus, initial_history: List[str]):
        self._opus = opus
        self._history = initial_history
        self._listeners: Dict[str, List[UIEventListener]] = {}
        self._websockets: List[WebSocketServerProtocol] = []

    def add_event_listener(self, event_name: str, listener: UIEventListener):
        """
        Add a listener to an event.

        Parameters
        ----------
        event_name
            The event to listen to
        listener
            A function to be executed when the event fires
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)

    def _emit(self, event_name: str):
        """
        Emit an event.

        Parameters
        ----------
        event_name
            The event to emit
        """
        for listener in self._listeners[event_name]:
            listener()

    def change_history(self, history: List[str]):
        """Update the history and send to clients."""
        self._history = history
        websockets.broadcast(self._websockets, json.dumps({
            "messageType": "history",
            "data": self._history
        }))

    async def handle_socket(self, websocket: WebSocketServerProtocol):
        """This handles one websocket connection."""
        self._websockets.append(websocket)
        # Handshake
        await websocket.send(json.dumps({
            "messageType": "nodes",
            "data": {key: asdict(node) for key, node in self._opus.nodes.items()}
        }))
        await websocket.send(json.dumps({
            "messageType": "history",
            "data": self._history
        }))
        base64_script = base64.b64encode(
            self._opus.script).decode("utf-8")
        await websocket.send(json.dumps({
            "messageType": "script",
            "data": f"data:application/pdf;base64,{base64_script}"
        }))
        # Handle messages from the client
        async for message in websocket:
            message_dict = json.loads(message)
            message_type = message_dict["messageType"]
            if message_type == "next-node":
                self._emit("next-node")
            else:
                print(f"WARNING: Unknown message type {message_type}")
        # Websocket is closed
        self._websockets.remove(websocket)

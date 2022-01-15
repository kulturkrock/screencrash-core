import base64
from dataclasses import asdict
import json
import traceback
from typing import List
import websockets
from websockets.server import WebSocketServerProtocol

from opus import Opus
from util.event_emitter import EventEmitter


class UI(EventEmitter):
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

    EFFECT_TYPES = {
        "unknown": 0,
        "audio": 1,
        "video": 2,
        "image": 3,
        "web": 4,
    }

    def __init__(self, opus: Opus, initial_history: List[str]):
        super().__init__()
        self._opus = opus
        self._history = initial_history
        self._effects = {}
        self._websockets: List[WebSocketServerProtocol] = []

    def changed_history(self, history: List[str]):
        """Update the history and send to clients."""
        self._history = history
        websockets.broadcast(self._websockets, json.dumps({
            "messageType": "history",
            "data": self._history
        }))

    def _send_effects_update(self):
        websockets.broadcast(self._websockets, json.dumps({
            "messageType": "effects",
            "data": list(self._effects.values())
        }))

    def effect_added(self, event_data):
        entity_id = event_data["entityId"]
        event_data["type"] = self.EFFECT_TYPES.get(event_data["effectType"], 0)
        del event_data["effectType"]
        self._effects[entity_id] = event_data
        self._send_effects_update()
    
    def effect_changed(self, event_data):
        entity_id = event_data["entityId"]
        event_data["type"] = self.EFFECT_TYPES.get(event_data["effectType"], 0)
        del event_data["effectType"]
        if not entity_id in self._effects:
            print(f"Tried to update effect {entity_id} but it doesnt exist. Skipping")
            return
        self._effects[entity_id].update(event_data)
        self._send_effects_update()
    
    def effect_removed(self, event_data):
        entity_id = event_data["entityId"]
        if entity_id in self._effects:
            del self._effects[entity_id]
            self._send_effects_update()
        else:
            print(f"Tried to remove effect but couldnt find it")

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
        await websocket.send(json.dumps({
            "messageType": "effects",
            "data": list(self._effects.values())
        }))
        base64_script = base64.b64encode(
            self._opus.script).decode("utf-8")
        await websocket.send(json.dumps({
            "messageType": "script",
            "data": f"data:application/pdf;base64,{base64_script}"
        }))
        # Handle messages from the client
        async for message in websocket:
            try:
                message_dict = json.loads(message)
                message_type = message_dict["messageType"]
                if message_type == "next-node":
                    self.emit("next-node")
                elif message_type == "choose-path":
                    choice_index = message_dict["choiceIndex"]
                    self.emit("choose-path", choice_index)
                elif message_type == "component-action":
                    target = message_dict["target_component"]
                    cmd = message_dict["cmd"]
                    asset_names = message_dict["assets"]
                    params = message_dict["params"]
                    self.emit("component-action", target, cmd, asset_names, params)
                else:
                    print(f"WARNING: Unknown message type {message_type}")
            except Exception as e:
                print(f"Failed to handle UI message. Got error {e}")
                traceback.print_exc()
        # Websocket is closed
        self._websockets.remove(websocket)

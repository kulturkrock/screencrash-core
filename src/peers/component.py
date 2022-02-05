import asyncio
import base64
from dataclasses import dataclass
import json
import threading
import traceback
from typing import Any, List, Dict
from opus import Asset
from util.event_emitter import EventEmitter
from peers.component_info import ComponentData, ComponentInfo

import websockets
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
        super().__init__()
        self._target_types = target_types
        self._websockets: List[WebSocketServerProtocol] = []
        self._assets: List[Asset] = []
        self._infos: Dict[str, ComponentData] = {}
    
    def add_asset(self, asset: Asset) -> None:
        self._assets.append(asset)

    async def handle_socket(self, websocket: WebSocketServerProtocol, initial_message: Any) -> None:
        """This handles one websocket connection."""
        self._websockets.append(websocket)
        # Request component info
        await websocket.send(json.dumps({"command": "req_component_info"}))
        # Sync files
        hashes = initial_message["files"]
        for asset in self._assets:
            if asset.data and hashes.get(asset.path) == asset.checksum:
                print(f"Asset {asset.path} already up to date")
            elif asset.data:
                print(f"Syncing asset {asset.path}")
                await websocket.send(json.dumps({"command": "file", "path": asset.path, 
                "data": base64.b64encode(asset.data).decode("utf-8")}))
            else:
                print(f"Skipping sync of asset {asset.path} (no data)")

        # Handle messages from the client
        component_id = None
        try:
            async for message in websocket:
                try:
                    message_dict = json.loads(message)
                    message_type = message_dict["messageType"]
                    if message_type == "heartbeat":
                        pass  # Ignore heartbeats for now
                    elif message_type == "component_info":
                        component_id = self.handle_component_info(message_dict, websocket)
                    else:
                        self.handle_component_message(message_type, message_dict)
                except Exception as e:
                    print(f"Failed to handle component message. Got error {e}")
                    traceback.print_exc()
        except websockets.exceptions.ConnectionClosedError as cce:
            print(f"Websocket to component closed abruptly: {cce}")

        # Websocket is closed
        if component_id:
            del self._infos[component_id]
            self.emit("disconnected", component_id)
        self._websockets.remove(websocket)

    def nof_instances(self) -> int:
        return len(self._websockets)

    def get_connected_clients(self) -> List[ComponentInfo]:
        return list(map(lambda comp: comp.info, self._infos.values()))

    def send_command(self, data) -> None:
        websockets.broadcast(self._websockets, json.dumps(data))

    def send_command_to(self, component_id, data):
        if self.has_component(component_id):
            def impl():
                websocket = self._infos[component_id].socket
                asyncio.run(websocket.send(json.dumps(data)))
            threading.Thread(target=impl).start()

    def has_component(self, component_id: str):
        return component_id in self._infos

    def reset_component(self, component_id: str):
        self.send_command_to(component_id, {
            "command": "reset",
            "channel": 1,
        })

    def handle_component_info(self, data, socket):
        component_info = ComponentInfo(**{k: v for k, v in data.items() if k != "messageType"})
        self._infos[component_info.componentId] = ComponentData(component_info, socket)
        self.emit("info-updated", component_info)
        return component_info.componentId

    def handles_target(self, target_type: str) -> bool:
        """Checks whether this instance can handle actions of the given type."""
        return target_type in self._target_types

    def handle_component_message(self, message_type: str, message: object) -> None:
        print(f"WARNING: Unknown message type {message_type}")

    def handle_action(self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, Any]) -> None:
        """Process the given action."""
        print(f"Command not handled by subclass: {target_type}:{cmd}")
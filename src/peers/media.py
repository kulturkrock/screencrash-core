from typing import Any, List, Dict
import random
from opus import Asset

from peers.component import ComponentPeer
from util.utilities import get_random_string


class MediaPeer(ComponentPeer):
    """
    Handles communication concerning media (video, audio, image, webpage etc).

    This has a websocket server that screens can connect to.

    Parameters
    ----------
    sync_assets
        Whether to sync assets
    """

    def __init__(self, sync_assets: bool):
        super().__init__(["image", "video", "web", "audio"], sync_assets)
        self._available_target_types = {}
        self._storages_random_cmds = {}

    def handle_component_message(self, component_id: str, message_type: str, message: object):
        if message_type == "effect-added":
            data = {key: value for key, value in message.items() if key !=
                    "messageType"}
            self.emit("effect-added", data)
        elif message_type == "effect-changed":
            data = {key: value for key, value in message.items() if key !=
                    "messageType"}
            self.emit("effect-changed", data)
        elif message_type == "effect-removed":
            entity_id = message["entityId"]
            self.emit("effect-removed", {"entityId": entity_id})
        else:
            super().handle_component_message(message_type, message)

    def handle_action(self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, Any]):
        """Process the given action."""

        entityId = params.get("entityId")
        if entityId is None:
            if cmd == "create" or cmd == "create_random":
                entityId = get_random_string(16)
            else:
                raise RuntimeError("Missing required parameter entityId")

        asset = assets[0].path if assets else None
        if cmd == "create_random":
            storage_id = params["storageId"]
            if storage_id not in self._storages_random_cmds:
                self._storages_random_cmds[storage_id] = []
            available_assets = list(map(lambda a: a.path, filter(lambda a: a.path not in self._storages_random_cmds[storage_id], assets)))
            if not available_assets:
                self._storages_random_cmds[storage_id] = []
                available_assets = assets.copy()
            random_asset = random.choice(available_assets)
            self._storages_random_cmds[storage_id].append(random_asset)
            asset = random_asset
            cmd = "create"


        data = {
            "command": cmd,
            "entityId": entityId,
            "channel": 1,
            "type": target_type,
            "asset": asset,
        }
        data.update(params)
        self.send_command(data)

from typing import Any, List, Dict
from opus import Asset

from peers.component import ComponentPeer
from util.utilities import get_random_string


class Screen(ComponentPeer):
    """
    Handles communication with screens.

    This has a websocket server that screens can connect to.

    Parameters
    ----------
    """

    def __init__(self):
        super().__init__(["image", "video"])
        self._entities = set()

    def _generate_id(self):
        while True:
            val = get_random_string(16)
            if not val in self._entities:
                return val

    def handle_component_message(self, message_type: str, message: object):
        if message_type == "cmd-error":
            print(f"Got an error from Screen Component: {message}")
        elif message_type == "effect-added":
            data = {key:value for key, value in message.items() if key != "messageType"}
            self.emit("effect-added", data)
        elif message_type == "effect-changed":
            data = {key:value for key, value in message.items() if key != "messageType"}
            self.emit("effect-changed", data)
        elif message_type == "effect-removed":
            entity_id = message["entityId"]
            self.emit("effect-removed", {"entityId": entity_id})
        else:
            super().handle_component_message(message_type, message)

    def handle_action(self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, Any]):
        """Process the given action."""
        if cmd == "create" or cmd == "start":
            if "entityId" not in params:
                params["entityId"] = self._generate_id()
            self._entities.add(params["entityId"])

        if cmd == "start":
            self._play_effect(target_type, assets[0], params)
        else:
            data = {
                "command": cmd,
                "entityId": params["entityId"],
                "channel": 1,
                "type": target_type,
                "asset": assets[0].path if assets else None,
            }
            data.update(params)
            self.send_to_all(data)

    def _play_effect(self, target_type: str, asset: Asset, params: Dict[str, Any]):
        # Combo of create, show and play.
        self.handle_action(target_type, "create", [asset], params)
        self.handle_action(target_type, "show", [], {"entityId": params["entityId"]})
        self.handle_action(target_type, "play", [], {"entityId": params["entityId"]})
from typing import List, Dict
from opus import Asset

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
        self._current_entity_id = 1

    def handle_action(self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, str]):
        """Process the given action."""
        if cmd == "start":
            self.play_effect(target_type, assets[0], params.get("autostart", True))
        else:
            super().handle_action(target_type, cmd, assets, params)

    def play_effect(self, target_type: str, asset: Asset, autostart=True):
        self.send_to_all({
            "command": "create",
            "entity_id": self._current_entity_id,
            "channel": 1,
            "type": target_type,
            "resource": asset.path
        })
        self.send_to_all({"command": "show", "entity_id": self._current_entity_id, "channel": 1})
        if autostart:
            self.send_to_all({"command": "play", "entity_id": self._current_entity_id, "channel": 1})
        self._current_entity_id += 1
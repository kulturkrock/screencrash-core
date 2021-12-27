from typing import List, Dict
from opus import Asset

from peers.component import ComponentPeer
from util.utilities import get_random_string


class Audio(ComponentPeer):
    """
    Handles communication with screens.

    This has a websocket server that screens can connect to.

    Parameters
    ----------
    """

    def __init__(self):
        super().__init__(["audio"])
        self._entities = []

    def _generate_id(self):
        while True:
            val = get_random_string(16)
            if not val in self._entities:
                return val
        
    def handle_component_message(self, message_type: str, message: object):
        if message_type == "cmd-error":
            print(f"Got an error from Audio Component: {message}")
        else:
            super().handle_component_message(message_type, message)

    def handle_action(self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, str]):
        """Process the given action."""
        if cmd == "start":
            self._add_sound(assets[0], params)
        elif cmd == "pause":
            self._pause_sound(params)
        elif cmd == "resume":
            self._play_sound(params)
        elif cmd == "stop":
            self._stop_sound(params)
        elif cmd == "set_volume":
            self._set_sound_volume(params)
        else:
            super().handle_action(target_type, cmd, assets, params)

    def _add_sound(self, asset: Asset, params: Dict[str, str]):
        entity_id = params.get("entity_id", self._generate_id())
        self.send_to_all({
            "command": "add",
            "entity_id": entity_id,
            "channel": 1,
            "path": asset.path,
            "loops": int(params.get("loops", "0")),
            "autostart": params.get("autostart", "true") == "true"
        })
        self._entities.append(entity_id)

    def _play_sound(self, params: Dict[str, str]):
        self.send_to_all({
            "command": "play",
            "entity_id": params["entity_id"],
            "channel": 1,
        })

    def _pause_sound(self, params: Dict[str, str]):
        self.send_to_all({
            "command": "pause",
            "entity_id": params["entity_id"],
            "channel": 1,
        })

    def _stop_sound(self, params: Dict[str, str]):
        self.send_to_all({
            "command": "stop",
            "entity_id": params["entity_id"],
            "channel": 1,
        })

    def _set_sound_volume(self, params: Dict[str, str]):
        if not params.get("volume_left") is None or not params.get("volume_right") is None:
            self.send_to_all({
                "command": "stop",
                "entity_id": params["entity_id"],
                "channel": 1,
                "volume_left": int(params.get("volume_left", "0")),
                "volume_right": int(params.get("volume_right", "0")),
            })
        else:
            self.send_to_all({
                "command": "stop",
                "entity_id": params["entity_id"],
                "channel": 1,
                "volume": int(params.get("volume", "0")),
            })

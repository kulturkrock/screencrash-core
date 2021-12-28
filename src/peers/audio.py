from typing import Any, List, Dict
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
        self._entities = set()

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

    def handle_action(self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, Any]):
        """Process the given action."""
        if cmd == "add":
            entity_id = params.get("entity_id", self._generate_id())
            self._entities.add(entity_id)
        else:
            entity_id = params.get("entity_id")

        data = {
            "command": cmd,
            "entity_id": entity_id,
            "channel": 1,
            "assets": [asset.path for asset in assets]
        }
        data.update(params)     # Add params to data

        self.send_to_all(data)

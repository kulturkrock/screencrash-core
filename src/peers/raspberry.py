from typing import Any, List, Dict
from opus import Asset

from peers.component import ComponentPeer


class RaspberryPeer(ComponentPeer):
    """
    Handles communication with raspberry component.

    Parameters
    ----------
    """

    def __init__(self):
        super().__init__(["raspberry"], False)

    def handle_component_message(
        self, component_id: str, message_type: str, message: object
    ):
        if message_type == "pong":
            print("got a pong")
        else:
            super().handle_component_message(message_type, message)

    def handle_component_disconnect(self, component_id):
        super().handle_component_disconnect(component_id)

    def handle_action(
        self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, Any]
    ):
        """Process the given action."""
        data = {"command": cmd, "channel": 1, "type": target_type}
        data.update(params)
        self.send_command(data)

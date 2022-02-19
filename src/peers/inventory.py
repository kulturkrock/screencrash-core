from typing import Any, List, Dict
from opus import Asset

from peers.component import ComponentPeer


class InventoryPeer(ComponentPeer):
    """
    Handles communication with inventory component.

    Parameters
    ----------
    """

    def __init__(self, sync_assets: bool):
        super().__init__(["inventory"], sync_assets)

    def handle_component_message(self, component_id: str, message_type: str, message: object):
        if message_type == "items":
            self.handle_component_state_update(component_id, { "items": message["items"] })
        elif message_type == "money":
            self.handle_component_state_update(component_id, { "money": message["money"] })
        elif message_type == "achievements":
            self.handle_component_state_update(component_id, { "achievemnents": message["achievements"] })
        elif message_type == "achievement_reached":
            # TODO: Handle event
            print("achievement reached")
        else:
            super().handle_component_message(message_type, message)

    def handle_action(self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, Any]):
        """Process the given action."""
        data = {
            "command": cmd,
            "channel": 1,
            "type": target_type
        }
        data.update(params)
        self.send_command(data)
from typing import List, Dict
from opus import Asset
from peers.component import ComponentPeer

class InternalPeer(ComponentPeer):

    def __init__(self):
        super().__init__(["internal"])

    def handle_action(self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, str]):
        """Process the given action."""
        if cmd == "print":
            print(params.get("text", "[print command found no text to print]"))
        else:
            super().handle_action(target_type, cmd, assets, params)
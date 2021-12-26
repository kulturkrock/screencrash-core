from typing import List, Dict
from opus import Asset
from .actor import Actor

class InternalActor(Actor):

    def __init__(self):
        super().__init__("internal")

    def handle_action(self, cmd: str, assets: List[Asset], params: Dict[str, str]):
        if cmd == "print":
            print(params.get("text", "[print command found no text to print]"))
        else:
            super().handle_action(cmd, assets, params)
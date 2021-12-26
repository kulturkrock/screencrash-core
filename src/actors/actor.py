
from typing import List, Dict
from opus import Asset
from util.event_emitter import EventEmitter


class Actor(EventEmitter):

    def __init__(self, target_type: str):
        self._target_type = target_type

    def handles_target(self, target_type: str):
        return self._target_type == target_type

    def handle_action(self, cmd: str, assets: List[Asset], params: Dict[str, str]):
        print("Command not handled by subclass: {}:{}".format(self._target_type, cmd))
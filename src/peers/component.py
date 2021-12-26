
from typing import List, Dict
from opus import Asset
from util.event_emitter import EventEmitter


class ComponentPeer(EventEmitter):
    """
    Base class for peers which accepts actions.

    Parameters
    ----------
    target_types
        Target types this peer listens too (e.g. audio, video, image etc.)
    """

    def __init__(self, target_types: List[str]):
        self._target_types = target_types

    def handles_target(self, target_type: str):
        """Checks whether this instance can handle actions of the given type."""
        return target_type in self._target_types

    def handle_action(self, target_type: str, cmd: str, assets: List[Asset], params: Dict[str, str]):
        """Process the given action."""
        print("Command not handled by subclass: {}:{}".format(target_type, cmd))
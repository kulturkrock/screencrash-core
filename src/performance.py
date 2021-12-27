from typing import Callable, List, Dict
from traceback import print_exception

from opus import Opus
from util.event_emitter import EventEmitter


class Performance(EventEmitter):
    """
    A performance in progress.

    It is responsible for keeping runtime state of a performance,
    and taking appropriate actions based on the current node.

    Parameters
    ----------
    opus
        The opus to perform
    """

    def __init__(self, opus: Opus):
        super().__init__()
        self._nodes = opus.nodes
        self.history = [opus.start_node]

    def next_node(self):
        """Go to the next node."""
        current_node = self._nodes[self.history[-1]]
        self.history.append(current_node.next)
        self.emit("history-changed", self.history)

        active_node = self._nodes[current_node.next]
        for action_id in active_node.actions:
            self.emit("run-action", action_id)

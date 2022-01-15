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
        if isinstance(current_node.next, str):
            print("Going to next node")
            next_node_id = current_node.next
            self.history.append(next_node_id)
            self.emit("history-changed", self.history)

            active_node = self._nodes[next_node_id]
            for action_id in active_node.actions:
                self.emit("run-action", action_id)
        else:
            print("Cannot go to next node, we're at a choice")

    def choose_path(self, choice_index: int):
        """Choose one of the next nodes."""
        current_node = self._nodes[self.history[-1]]
        if isinstance(current_node.next, str):
            print(f"Tried to choose node number {choice_index}, but there is no choice here")
        elif choice_index >= len(current_node.next) or choice_index < 0:
            print(f"Tried to choose node number {choice_index}, but it does not exist")
        else:
            print(f"Choosing node number {choice_index}")
            next_node_id = current_node.next[choice_index].node
            self.history.append(next_node_id)
            self.emit("history-changed", self.history)

            active_node = self._nodes[next_node_id]
            for action_id in active_node.actions:
                self.emit("run-action", action_id)
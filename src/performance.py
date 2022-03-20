from typing import Callable, List, Dict
from traceback import print_exception

from opus import EventTrigger, Opus
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
        self._event_triggers = opus.event_triggers
        self.history = [opus.start_node]

    def next_node(self, run_actions: bool):
        """Go to the next node."""
        current_node = self._nodes[self.history[-1]]
        if isinstance(current_node.next, str):
            if run_actions:
                self.run_actions()

            print("Going to next node")
            next_node_id = current_node.next
            self.history.append(next_node_id)
            self.emit("history-changed", self.history)
        else:
            print("Cannot go to next node, we're at a choice")

    def prev_node(self):
        """Go to the prev node (edit history)"""
        if len(self.history) > 1:
            self.history.pop(-1)
            self.emit("history-changed", self.history)
        else:
            print("Cannot go to prev node, history is too short")

    def run_actions(self):
        """Runs the actions on the current node"""
        active_node = self._nodes[self.history[-1]]
        for action_id in active_node.actions:
            self.emit("run-action", action_id)

    def choose_path(self, choice_index: int, run_actions: bool):
        """Choose one of the next nodes."""
        current_node = self._nodes[self.history[-1]]
        if isinstance(current_node.next, str):
            print(f"Tried to choose node number {choice_index}, but there is no choice here")
        elif choice_index >= len(current_node.next) or choice_index < 0:
            print(f"Tried to choose node number {choice_index}, but it does not exist")
        else:
            print(f"Choosing node number {choice_index}")
            if run_actions:
                for action_id in current_node.actions:
                    self.emit("run-action", action_id)
                for action_id in current_node.next[choice_index].actions:
                    self.emit("run-action", action_id)

            next_node_id = current_node.next[choice_index].node
            self.history.append(next_node_id)
            self.emit("history-changed", self.history)

    def on_component_event(self, component_type: str, event: str, params: Dict[str, str]) -> None:
        print(f"Got event {component_type} {event} {params}")
        for event_trigger in self._event_triggers:
            if self._matches_event_trigger(event_trigger, component_type, event, params):
                for action_id in event_trigger.actions:
                    self.emit("run-action", action_id)

    def _matches_event_trigger(self, event_trigger: EventTrigger, component_type: str, event: str, params: Dict[str, str]) -> bool:
        if event_trigger.target != component_type:
            return False
        if not self._matches_event_string(event_trigger.event, event):
            return False
        for param in event_trigger.params:
            expected_result = False if param.inverted else True
            if param.name not in params:
                return False
            if self._matches_event_string(param.expression, params[param.name]) != expected_result:
                return False
        return True

    def _matches_event_string(self, expected_value: str, value: str):
        if expected_value == "any":
            return value is not None
        elif "|" in expected_value:
            return value in expected_value.split("|")
        else:
            return value == expected_value
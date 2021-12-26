from typing import Callable, List, Dict
from traceback import print_exception

from opus import Opus
from util.event_emitter import EventEmitter
from actors.actor import Actor


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

    def __init__(self, opus: Opus, actors: List[Actor]):
        super().__init__()
        self._action_templates = opus.action_templates
        self._assets = opus.assets
        self._nodes = opus.nodes
        self.history = [opus.start_node]
        self._actors = actors

    def _warning(self, msg):
        print("Warning: {}".format(msg))
        self.emit("warning", msg)

    def next_node(self):
        """Go to the next node."""
        current_node = self._nodes[self.history[-1]]
        self.history.append(current_node.next)
        self.emit("history-changed", self.history)

        active_node = self._nodes[current_node.next]
        for action_id in active_node.actions:
            try:
                self._run_action(action_id)
            except Exception as e:
                self._warning("Failed to carry out action: {}".format(e))
                print_exception(e)

    def _run_action(self, action_id):
        action = self._action_templates.get(action_id)
        if action is None:
            print("Failed to find action with id {}. Skipping.".format(action_id))
            return

        assets = [self._assets[key] for key in action.assets]
        handled = False
        for actor in self._actors:
            if actor.handles_target(action.target):
                actor.handle_action(action.cmd, assets, action.params)
                handled = True

        if not handled:
            self._warning("Action not handled by any actor")

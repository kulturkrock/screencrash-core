from typing import Callable, List, Dict

from opus import Opus

# Only history-changed so far
PerformanceEventListener = Callable[[List[str]], None]


class Performance:
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
        self._nodes = opus.nodes
        self.history = [opus.start_node]
        self._listeners: Dict[str, List[PerformanceEventListener]] = {}

    def add_event_listener(self, event_name: str, listener: PerformanceEventListener):
        """
        Add a listener to an event.

        Parameters
        ----------
        event_name
            The event to listen to
        listener
            A function to be executed when the event fires
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)

    def _emit(self, event_name: str, *args):
        """
        Emit an event.

        Parameters
        ----------
        event_name
            The event to emit
        """
        for listener in self._listeners.get(event_name, []):
            listener(*args)

    def next_node(self):
        """Go to the next node."""
        current_node = self._nodes[self.history[-1]]
        self.history.append(current_node.next)
        self._emit("history-changed", self.history)

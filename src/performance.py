from opus import Opus


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

    def next_node(self):
        """Go to the next node."""
        current_node = self._nodes[self.history[-1]]
        self.history.append(current_node.next)

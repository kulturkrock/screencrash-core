import asyncio
import base64
from dataclasses import asdict
import json
from pathlib import Path
import websockets

from opus import load_opus
from performance import Performance
from peers.ui import UI


class Core:
    """This is the main class, keeping track of all state."""

    async def main(self):
        """The main loop."""
        self._opus = await load_opus(Path("resources") / "dev_opus.yaml")
        self._performance = Performance(self._opus)
        self._ui = UI(self._opus, self._performance.history, 8001)
        self._ui.add_event_listener("next-node", self.handle_next_node)
        await self._ui.run()  # Blocks forever

    def handle_next_node(self):
        """Handle the UI going to the next node."""
        self._performance.next_node()
        self._ui.change_history(self._performance.history)


if __name__ == "__main__":
    core = Core()
    try:
        asyncio.run(core.main())
    except KeyboardInterrupt:
        print('Exiting')

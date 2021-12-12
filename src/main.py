import asyncio
import base64
from dataclasses import asdict
import json
from pathlib import Path
import websockets

from opus import load_opus


class Core:
    """This is the main class, keeping track of all state."""

    async def main(self):
        """The main loop."""
        self._opus = await load_opus(Path("resources") / "dev_opus.yaml")
        self._history = [self._opus.start_node]
        async with websockets.serve(self.socket_listener, "localhost", 8001):
            await asyncio.Future()  # run forever

    async def socket_listener(self, websocket, path):
        """This handles one websocket connection."""
        # Handshake
        await websocket.send(json.dumps({
            "messageType": "nodes",
            "data": {key: asdict(node) for key, node in self._opus.nodes.items()}
        }))
        await websocket.send(json.dumps({
            "messageType": "history",
            "data": self._history
        }))
        base64_script = base64.b64encode(
            self._opus.script).decode("utf-8")
        await websocket.send(json.dumps({
            "messageType": "script",
            "data": f"data:application/pdf;base64,{base64_script}"
        }))
        # Handle messages from the client
        async for message in websocket:
            message_dict = json.loads(message)
            message_type = message_dict["messageType"]
            if message_type == "next-node":
                current_node = self._opus.nodes[self._history[-1]]
                self._history.append(current_node.next)
                await websocket.send(json.dumps({"messageType": "history", "data": self._history}))
            else:
                print(f"WARNING: Unknown message type {message_type}")


if __name__ == "__main__":
    core = Core()
    try:
        asyncio.run(core.main())
    except KeyboardInterrupt:
        print('Exiting')

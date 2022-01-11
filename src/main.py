import asyncio
import json
from typing import Dict
import os
from pathlib import Path
import websockets
from websockets.server import WebSocketServerProtocol

from opus import ActionTemplate, load_opus
from peers.component import ComponentPeer
from performance import Performance
from peers.audio import Audio
from peers.internal import InternalPeer
from peers.screen import Screen
from peers.ui import UI


class Core:
    """
    This is the main class, keeping track of all state.

    Parameters
    ----------
    port
        The port to run a websocket server on
    """

    def __init__(self, port: int):
        self._port = port

    async def main(self):
        """The main loop."""
        opus_file = os.environ.get("OPUS", "dev_opus.yaml")
        print("Loading opus...")
        self._opus = await load_opus(Path("resources") / opus_file)
        self._performance = Performance(self._opus)
        self._ui = UI(self._opus, self._performance.history)
        self._components: Dict[str,ComponentPeer] = {
            "internal": InternalPeer(),
            "screen": Screen(),
            "audio": Audio()
        }
        self._setup_events()
        self._distribute_assets()

        print("Started!")
        async with websockets.serve(self.socket_listener, "0.0.0.0", self._port):
            await asyncio.Future()  # run forever

    def _setup_events(self):
        self._ui.add_event_listener("next-node", self._performance.next_node)
        self._ui.add_event_listener("component-action", self._run_action_on_the_fly)
        self._performance.add_event_listener("history-changed", self._ui.changed_history)
        self._performance.add_event_listener("run-action", self._run_action_by_id)

        for component in self._components.values():
            component.add_event_listener("effect-added", self._ui.effect_added)
            component.add_event_listener("effect-changed", self._ui.effect_changed)
            component.add_event_listener("effect-removed", self._ui.effect_removed)
            component.add_event_listener("info-updated", self._ui.component_updated)
            component.add_event_listener("disconnected", self._ui.component_removed)
    
    def _distribute_assets(self):
        for asset in self._opus.assets.values():
            for component in self._components.values():
                if any([component.handles_target(target) for target in asset.targets]):
                    component.add_asset(asset)
    
    def _run_action_by_id(self, action_id):
        try:
            action = self._opus.action_templates[action_id]
            assets = [self._opus.assets[key] for key in action.assets]
            self._run_action(action, assets)
        except KeyError:
            print(f"Failed to find action or asset for action {action_id}. Skipping.")
            return

    def _run_action_on_the_fly(self, target, cmd, asset_names, params):
        action = ActionTemplate(1337, target, cmd, asset_names, params)
        assets = [self._opus.assets[name] for name in asset_names]
        self._run_action(action, assets)

    def _run_action(self, action, assets):
        handled = False
        for peer in self._components.values():
            if peer.handles_target(action.target) and peer.nof_instances() > 0:
                try:
                    peer.handle_action(action.target, action.cmd, assets, action.params)
                    handled = True
                except Exception as e:
                    print(f"Failed to run handle_action: {e}")
        if not handled:
            print(f"Warning: Action {action.id} not handled by anyone ({action.target})")

    async def socket_listener(self, websocket: WebSocketServerProtocol):
        """
        This function handles an incoming websocket connection.

        Parameters
        ----------
        websocket
            The websocket
        """
        # Wait for a hello
        message = await websocket.recv()
        message_dict = json.loads(message)
        client_type = message_dict["client"]
        if client_type == "ui":
            await self._ui.handle_socket(websocket)
        elif client_type in self._components:
            print(f"Accepted client of type {client_type}")
            await self._components[client_type].handle_socket(websocket, message_dict)
        else:
            print(f"An unsupported client type tried to connect: {client_type}")


if __name__ == "__main__":
    core = Core(8001)
    try:
        asyncio.run(core.main())
    except KeyboardInterrupt:
        print('Exiting')

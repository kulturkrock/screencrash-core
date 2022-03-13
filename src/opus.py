import asyncio
from dataclasses import dataclass, field
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import re
import sys
import aiofiles
import fitz
import yaml

# TODO: Autodiscover these instead of hard-coding them, in case
# the script looks different in the future.
LEFT_PAGE_LINE_NUMBER_END = (76, 77)
RIGHT_PAGE_LINE_NUMBER_END = (62, 63)


@dataclass
class Asset:
    """An asset contains a resource"""
    path: str
    data: Optional[bytes]
    checksum: Optional[str]
    targets: List[str]


@dataclass
class ActionTemplate:
    """An Action is a command triggered by a node"""
    id: str
    target: str
    cmd: str
    desc: Optional[str] = None
    assets: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeChoice:
    """One choice of node when the opus branches"""
    node: str
    description: str
    actions: List[str] = field(default_factory=list)


@dataclass
class Node:
    """A Node is a single location in the script."""
    next: Optional[Union[str, List[NodeChoice]]]
    prompt: str
    pdfPage: int
    pdfLocationOnPage: float
    actions: List[str] = field(default_factory=list)
    lineNumber: Optional[int] = None


@dataclass
class Opus:
    """An Opus has all the information required for a performance."""
    nodes: Dict[str, Node]
    action_templates: Dict[str, ActionTemplate]
    assets: Dict[str, Asset]
    start_node: str
    script: bytes


async def load_opus(opus_path: Path, read_asset_data: bool, exit_on_validation_failure: bool):
    """Load an opus from a file."""
    parent = opus_path.parent
    async with aiofiles.open(opus_path, mode="r", encoding="utf-8") as f:
        opus_string = await f.read()
        opus_dict = yaml.safe_load(opus_string)
        nodes, inlined_action_dicts = await load_nodes(opus_dict["nodes"], parent / opus_dict["assets"]["script"]["path"])
        action_templates, inlined_asset_dicts = load_actions(
            {**opus_dict["action_templates"], **inlined_action_dicts})
        assets = dict(await asyncio.gather(
            *[load_asset(key, asset["path"], action_templates, opus_path, read_asset_data)
              for key, asset in [*opus_dict["assets"].items(), *inlined_asset_dicts.items()]]
        ))
        if assets.get("script") is None:
            raise RuntimeError(
                "Warning: Asset 'script' not found. This is required.")
        start_node = opus_dict["startNode"]

    async with aiofiles.open(parent / assets["script"].path, mode="rb") as f:
        script = await f.read()

    opus = Opus(nodes, action_templates, assets, start_node, script)
    validate_references(opus, exit_on_validation_failure)
    return opus


async def load_asset(key: str, path: str, action_templates: Dict[str, ActionTemplate], opus_path: Path, read_asset_data: bool):
    """
    Load an asset from a file.

    Parameters
    ----------
    key
        The ID of the asset. Used for checking where it is used.
    path
        The path to the file, relative to the opus path
    action_templates
        All action templates in the opus. Used for checking where the asset is used.
    opus_path
        The path to the opus file
    read_asset_data
        Whether to read the asset data from the file

    Returns
    -------
    A list of tuples (key, asset)
    """
    targets = set(
        action.target for action in action_templates.values() if key in action.assets)
    data = None
    checksum = None
    if read_asset_data and not path.startswith("http://") and not path.startswith("https://"):
        async with aiofiles.open(opus_path.parent / path, mode="rb") as f:
            data = await f.read()
        checksum = hashlib.md5(data).hexdigest()
    return (key, Asset(path=path, data=data, checksum=checksum, targets=targets))


def load_actions(action_dicts: Dict[str, dict]) -> Tuple[Dict[str, ActionTemplate], Dict[str, dict]]:
    """
    Load actions, and pick out inlined assets.

    Parameters
    ----------
    action_dicts
        Dict of actions, as found in the opus

    Returns
    -------
    Dict of actions, converted to ActionTemplates, and a dict of inlined assets
    """
    actions = {}
    assets = {}
    for key, action_dict in action_dicts.items():
        typed_action_dict = action_dict.copy()
        if "assets" in typed_action_dict:
            for i, asset in enumerate(typed_action_dict["assets"]):
                if isinstance(asset, dict):
                    asset_id = f"{key}_asset_{i}"
                    assets[asset_id] = asset
                    typed_action_dict["assets"][i] = asset_id
        actions[key] = ActionTemplate(id=key, **typed_action_dict)
    return actions, assets


async def load_nodes(nodes_dict: Dict[str, dict], script_path: Path) -> Tuple[Dict[str, Node], Dict[str, dict]]:
    """
    Load the nodes, find their locations on the page, and pick out inlined actions.

    If a node does not already have a defined lineNumber, it will be given one.
    Then we assume the node ID begins with the line number, e.g. "12" or "13a".

    If a node does not already have defined pdfPage and pdfLocationOnPage,
    we will try to find it in the PDF based on the line number.

    Parameters
    ----------
    nodes_dict
        The nodes from the opus file
    script_path
        Path to the script PDF

    Returns
    -------
    The nodes and the inlined actions
    """
    # Get line numbers
    for key, node in nodes_dict.items():
        if "lineNumber" not in node:
            try:
                line_number = re.match(r"[0-9]+", key).group(0)
                node["lineNumber"] = int(line_number)
            except AttributeError:
                pass  # lineNumber is not mandatory

    doc = fitz.open(script_path)
    # Get all node keys where we need to discover the location.
    node_keys = [
        key for key, value in nodes_dict.items()
        if "pdfPage" not in value or "pdfLocationOnPage" not in value
    ]
    if len(node_keys) > 0:
        try:
            with_line_numbers = [(key, nodes_dict[key]["lineNumber"])
                                 for key in node_keys]
        except KeyError:
            raise RuntimeError(
                "Nodes without specified PDF locations must have IDs beginning with numbers, "
                "or defined lineNumber. "
                f"Offenders: {[key for key in node_keys if 'lineNumber' not in nodes_dict[key]]}"
            )
        sorted_keys_and_numbers = sorted(
            with_line_numbers, key=lambda x: int(x[1]))
        next_pair = sorted_keys_and_numbers.pop(0)
        # Searching for e.g. "12" will find both "12" and "112". Since the wanted line numbers
        # are sorted, the first occurrence we find is correct.
        for page in doc:
            while True:
                key, line_number = next_pair
                found = [
                    rect for rect in page.search_for(str(line_number))
                    if (LEFT_PAGE_LINE_NUMBER_END[0] < rect.x1 < LEFT_PAGE_LINE_NUMBER_END[1])
                    or (RIGHT_PAGE_LINE_NUMBER_END[0] < rect.x1 < RIGHT_PAGE_LINE_NUMBER_END[1])
                ]
                if len(found) == 0:
                    # We won't find anything more on this page, since the wanted line numbers are sorted
                    break
                nodes_dict[key]["pdfPage"] = page.number
                y = (found[0].y0 + found[0].y1) / 2
                nodes_dict[key]["pdfLocationOnPage"] = y / page.rect.y1
                if len(sorted_keys_and_numbers) == 0:
                    next_pair = None
                    break
                next_pair = sorted_keys_and_numbers.pop(0)
            if next_pair is None:
                break

    # Convert nodes from dicts to Node objects, and pick out all inlined actions.
    # We make up action IDs.
    nodes = {}
    action_dicts = {}
    for key, node in nodes_dict.items():
        typed_node = node.copy()
        if isinstance(typed_node.get("next"), list):
            for i, choice in enumerate(typed_node["next"]):
                if "actions" in choice:
                    for j, action in enumerate(choice["actions"]):
                        if isinstance(action, dict):
                            action_id = f"{key}_choice_{i}_action_{j}"
                            action_dicts[action_id] = action
                            choice["actions"][j] = action_id
                typed_node["next"][i] = NodeChoice(**choice)
        if "actions" in typed_node:
            for i, action in enumerate(typed_node["actions"]):
                if isinstance(action, dict):
                    action_id = f"{key}_action_{i}"
                    action_dicts[action_id] = action
                    typed_node["actions"][i] = action_id
        nodes[key] = Node(**typed_node)

    return nodes, action_dicts


def validate_references(opus: Opus, exit_on_failure: bool):
    """
    Validate that we only refer to existing nodes, assets and actions.

    Exits the program if validation fails.

    Parameters
    ----------
    opus
        The opus
    exit_on_failure
        Whether to exit the program if validation fails
    """
    # Nodes
    referred_nodes = set([opus.start_node])
    for node in opus.nodes.values():
        if isinstance(node.next, str):
            referred_nodes.add(node.next)
        elif isinstance(node.next, list):
            for choice in node.next:
                referred_nodes.add(choice.node)
    actual_nodes = set(opus.nodes.keys())
    if referred_nodes != actual_nodes:
        nonexistent_nodes = referred_nodes - actual_nodes
        unreferred_nodes = actual_nodes - referred_nodes
        print("Malformed opus!")
        if nonexistent_nodes:
            print("References to nonexistent nodes:")
            print('\n'.join(nonexistent_nodes))
        if unreferred_nodes:
            print("Nodes never referred to:")
            print('\n'.join(unreferred_nodes))
        if exit_on_failure:
            print("Aborting!")
            sys.exit(1)

    # Assets
    referred_assets = set(["script"])
    for action in opus.action_templates.values():
        referred_assets.update(set(action.assets))
    actual_assets = set(opus.assets.keys())
    if referred_assets != actual_assets:
        nonexistent_assets = referred_assets - actual_assets
        unreferred_assets = actual_assets - referred_assets
        print("Malformed opus!")
        if nonexistent_assets:
            print("References to nonexistent assets:")
            print('\n'.join(nonexistent_assets))
        if unreferred_assets:
            print("Assets never referred to:")
            print('\n'.join(unreferred_assets))
        if exit_on_failure:
            print("Aborting!")
            sys.exit(1)

    # Actions
    referred_actions = set()
    for node in opus.nodes.values():
        if node.actions is not None:
            referred_actions.update(set(node.actions))
        if isinstance(node.next, list):
            for choice in node.next:
                if choice.actions is not None:
                    referred_actions.update(set(choice.actions))
    actual_actions = set(opus.action_templates.keys())
    if referred_actions != actual_actions:
        nonexistent_actions = referred_actions - actual_actions
        unreferred_actions = actual_actions - referred_actions
        print("Malformed opus!")
        if nonexistent_actions:
            print("References to nonexistent actions:")
            print('\n'.join(nonexistent_actions))
        if unreferred_actions:
            print("Actions never referred to:")
            print('\n'.join(unreferred_actions))
        if exit_on_failure:
            print("Aborting!")
            sys.exit(1)

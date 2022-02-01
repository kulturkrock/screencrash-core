import asyncio
from dataclasses import dataclass, field
import hashlib
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import re
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
    id: int
    target: str
    cmd: str
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


@dataclass
class Opus:
    """An Opus has all the information required for a performance."""
    nodes: Dict[str, Node]
    action_templates: Dict[str, ActionTemplate]
    assets: Dict[str, Asset]
    start_node: str
    script: bytes


async def load_opus(opus_path: Path):
    """Load an opus from a file."""
    parent = opus_path.parent
    async with aiofiles.open(opus_path, mode="r", encoding="utf-8") as f:
        opus_string = await f.read()
        opus_dict = yaml.safe_load(opus_string)
        action_templates = {key: ActionTemplate(
            id=key, **action) for key, action in opus_dict["action_templates"].items()}
        assets = dict(await asyncio.gather(
            *[load_asset(key, asset["path"], action_templates, opus_path)
              for key, asset in opus_dict["assets"].items()]
        ))
        if assets.get("script") is None:
            raise RuntimeError(
                "Warning: Asset 'script' not found. This is required.")
        nodes = await load_nodes(opus_dict["nodes"], parent / assets["script"].path)
        start_node = opus_dict["startNode"]

    async with aiofiles.open(parent / assets["script"].path, mode="rb") as f:
        script = await f.read()

    return Opus(nodes, action_templates, assets, start_node, script)


async def load_asset(key: str, path: str, action_templates: Dict[str, ActionTemplate], opus_path: Path):
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

    Returns
    -------
    A list of tuples (key, asset)
    """
    targets = set(
        action.target for action in action_templates.values() if key in action.assets)
    data = None
    checksum = None
    if not path.startswith("http://") and not path.startswith("https://"):
        async with aiofiles.open(opus_path.parent / path, mode="rb") as f:
            data = await f.read()
        checksum = hashlib.md5(data).hexdigest()
    return (key, Asset(path=path, data=data, checksum=checksum, targets=targets))


async def load_nodes(nodes_dict: Dict[str, Any], script_path: Path) -> Dict[str, Node]:
    """
    Load the nodes, and find their locations on the page.

    If a node does not already have defined pdfPage and pdfLocationOnPage,
    we will try to find it in the PDF. If so, we assume the node ID begins
    with the line number, e.g. "12" or "13a".

    Parameters
    ----------
    nodes_dict
        The nodes from the opus file
    script_path
        Path to the script PDF

    Returns
    -------
    The nodes
    """
    doc = fitz.open(script_path)
    # Get all node keys where we need to discover the location.
    node_keys = [
        key for key, value in nodes_dict.items()
        if "pdfPage" not in value or "pdfLocationOnPage" not in value
    ]
    if len(node_keys) > 0:
        try:
            with_line_numbers = [(key, re.match(r"[0-9]+", key).group(0))
                                for key in node_keys]
        except AttributeError:
            raise RuntimeError(
                "Nodes without specified PDF locations must have IDs beginning with numbers. "
                f"Offenders: {[key for key in node_keys if re.match(r'[0-9]+', key) is None]}"
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
                    rect for rect in page.search_for(line_number)
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
    
    nodes = {}
    for key, node in nodes_dict.items():
        typed_node = node.copy()
        if isinstance(typed_node.get("next"), list):
            typed_node["next"] = [NodeChoice(
                **node_choice) for node_choice in node["next"]]
        nodes[key] = Node(**typed_node)
    return nodes

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import aiofiles
import yaml

@dataclass
class Asset:
    """An asset describes a resource file"""
    path: str


@dataclass
class ActionTemplate:
    """An Action is a command triggered by a node"""
    id: int
    target: str
    cmd: str
    assets: List[str] = field(default_factory=lambda: [])
    params: Dict[str, str] = field(default_factory=lambda: {})


@dataclass
class Node:
    """A Node is a single location in the script."""
    next: str
    prompt: str
    pdfPage: int
    pdfLocationOnPage: float
    actions: List[int]


@dataclass
class Opus:
    """An Opus has all the information required for a performance."""
    nodes: Dict[str, Node]
    action_templates: Dict[int, ActionTemplate]
    assets: Dict[str, Asset]
    start_node: str
    script: bytes


async def load_opus(opus_path: Path):
    """Load an opus from a file."""
    parent = opus_path.parent
    async with aiofiles.open(opus_path, mode="r") as f:
        opus_string = await f.read()
        opus_dict = yaml.safe_load(opus_string)
        assets = {key: Asset(**asset) for key, asset in opus_dict["assets"].items()}
        action_templates = {int(key): ActionTemplate(id=int(key), **action) for key, action in opus_dict["action_templates"].items()}
        nodes = {key: Node(**node) for key, node in opus_dict["nodes"].items()}
        start_node = opus_dict["startNode"]

    if assets.get("script") is None:
        print("Warning: Asset 'script' not found. This is required.")
    async with aiofiles.open(parent / assets["script"].path, mode="rb") as f:
        script = await f.read()

    return Opus(nodes, action_templates, assets, start_node, script)

import asyncio
from dataclasses import dataclass, field
import hashlib
from typing import Any, Dict, List, Optional
from pathlib import Path
import aiofiles
import yaml

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
class Node:
    """A Node is a single location in the script."""
    next: str
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
        action_templates = {key: ActionTemplate(id=key, **action) for key, action in opus_dict["action_templates"].items()}
        assets = dict(await asyncio.gather(
            *[load_asset(key, asset["path"], action_templates, opus_path)
              for key, asset in opus_dict["assets"].items()]
        ))
        nodes = {key: Node(**node) for key, node in opus_dict["nodes"].items()}
        start_node = opus_dict["startNode"]

    if assets.get("script") is None:
        raise RuntimeError("Warning: Asset 'script' not found. This is required.")
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
    targets = set(action.target for action in action_templates.values() if key in action.assets)
    data = None
    checksum = None
    if not path.startswith("http://") and not path.startswith("https://"):
        async with aiofiles.open(opus_path.parent / path, mode="rb") as f:
            data = await f.read()
        checksum=hashlib.md5(data).hexdigest()
    return (key, Asset(path=path, data=data, checksum=checksum, targets=targets))

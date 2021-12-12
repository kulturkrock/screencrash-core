from dataclasses import dataclass
from typing import Dict
from pathlib import Path
import aiofiles
import yaml


@dataclass
class Node:
    """A Node is a single location in the script."""
    next: str
    prompt: str
    pdfPage: int
    pdfLocationOnPage: float


@dataclass
class Opus:
    """An Opus has all the information required for a performance."""
    nodes: Dict[str, Node]
    start_node: str
    script: bytes


async def load_opus(opus_path: Path):
    """Load an opus from a file."""
    parent = opus_path.parent
    async with aiofiles.open(opus_path, mode="r") as f:
        opus_string = await f.read()
        opus_dict = yaml.safe_load(opus_string)
        nodes = {key: Node(**node) for key, node in opus_dict["nodes"].items()}
        start_node = opus_dict["startNode"]
    async with aiofiles.open(parent / opus_dict["scriptFile"], mode="rb") as f:
        script = await f.read()
    return Opus(nodes, start_node, script)

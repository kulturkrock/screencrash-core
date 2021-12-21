from dataclasses import dataclass, field
from typing import Dict, List
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
    playEffects: List[str] = field(default_factory=list)


@dataclass
class Effect:
    """An effect that can be played."""
    type: str
    file: Path


@dataclass
class Opus:
    """An Opus has all the information required for a performance."""
    nodes: Dict[str, Node]
    start_node: str
    script: bytes
    effects: Dict[str, Effect]


async def load_opus(opus_path: Path):
    """Load an opus from a file."""
    parent = opus_path.parent.absolute()
    async with aiofiles.open(opus_path, mode="r") as f:
        opus_string = await f.read()
        opus_dict = yaml.safe_load(opus_string)
        nodes = {key: Node(**node) for key, node in opus_dict["nodes"].items()}
        start_node = opus_dict["startNode"]
        effects = {
            key: Effect(type=effect["type"], file=parent / effect["file"])
            for key, effect in opus_dict["effects"].items()
        }
    async with aiofiles.open(parent / opus_dict["scriptFile"], mode="rb") as f:
        script = await f.read()
    return Opus(nodes, start_node, script, effects)

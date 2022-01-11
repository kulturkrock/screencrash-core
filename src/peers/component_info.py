from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class ComponentCommandParam:
    name: str
    type: str   # string, number, boolean, raw
    desc: str
    default: Any
    required: bool


@dataclass
class ComponentCommand:
    cmd: str
    desc: str
    params: List[ComponentCommandParam]


@dataclass
class ComponentInfo:
    componentId: str
    componentName: str
    commands: Dict[str, List[ComponentCommand]]

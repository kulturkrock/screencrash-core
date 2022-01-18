from dataclasses import dataclass


@dataclass
class ComponentInfo:
    componentId: str
    componentName: str
    status: str

from dataclasses import dataclass


from websockets.server import WebSocketServerProtocol

@dataclass
class ComponentInfo:
    componentId: str
    componentName: str
    status: str
    

@dataclass
class ComponentData:
    info: ComponentInfo
    socket: WebSocketServerProtocol

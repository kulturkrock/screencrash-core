
from actors.internal import InternalActor
from actors.audio import AudioActor
from actors.video import VideoActor

def create_actor(component):
    if component.type == "audio":
        return AudioActor()
    elif component.type == "internal":
        return InternalActor()
    elif component.type == "video":
        return VideoActor()
    else:
        print("Unknown component type: {}".format(component.type))
    return None
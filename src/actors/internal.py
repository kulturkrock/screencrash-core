from .actor import Actor

class InternalActor(Actor):

    def __init__(self):
        super().__init__("internal")

    def handle_action(self, cmd, assets, params):
        if cmd == "print":
            print(params.get("text", "[print command found no text to print]"))
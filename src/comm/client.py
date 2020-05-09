
from .connection import ConnectionBase


class Client:

    def __init__(self, connection: ConnectionBase):
        self.connection = connection
        self.connection.client = self
        self.subscriptions = set()

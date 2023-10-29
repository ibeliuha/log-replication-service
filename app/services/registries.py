from models.models import Message, SecondaryServer, ServerStatus
import collections


class MessageRegistry(collections.OrderedDict):
    message_id: int = 0
    awaited_messages: dict = dict()

    def __init__(self):
        super().__init__()

    def register(self, message: Message) -> int:
        self.message_id += 1
        self[self.message_id] = message.register(message_id=self.message_id)

        return self.message_id

    def add(self, message: Message) -> int:
        """
        message added in order using message.meta.id attribute using recursive exhaustion
        """
        self.awaited_messages[message.meta.message_id] = message
        self._exhaust_awaited_list()
        return message.meta.message_id

    def _exhaust_awaited_list(self):
        try:
            self[self.message_id+1] = self.awaited_messages.pop(self.message_id+1)
            self.message_id += 1
            self._exhaust_awaited_list()
        except KeyError:
            return

    def dict(self) -> dict:
        result = {}
        for key, value in self.items():
            result[key] = value.dict()
        return result

    def list(self):
        return [value.dict() for key, value in self.items()]


class ServiceRegistry(collections.UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.servers_number: int = 0
        self.healthy_servers_number: int = 0

    def register(self, service: SecondaryServer) -> str:
        self[service.id] = service
        self.servers_number += 1
        self.healthy_servers_number += 1
        return service.id

    def remove(self, server_id: str):
        self.pop(server_id)
        self.servers_number -= 1
        self.healthy_servers_number -= 1

    def change_status(self, server_id: str, new_status: ServerStatus):
        if self[server_id].status == new_status:
            return
        self.healthy_servers_number += new_status.value-self[server_id].status.value
        self[server_id].status = new_status

    def dict(self) -> dict:
        result = {}
        for key, value in self.items():
            result[key] = value.dict()
        return result

    def list(self) -> list:
        return [value.dict() for key, value in self.items()]





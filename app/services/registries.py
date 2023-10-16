from models.models import Message, SecondaryServer, ServerStatus
import collections


class MessageRegistry(collections.OrderedDict):
    message_id: int = 0

    def __init__(self):
        super().__init__()

    def register(self, message: Message) -> int:
        if not isinstance(message, Message):
            raise Exception()
        message_id = self.next()
        self[message_id] = message.register(message_id=message_id)

        return self.message_id

    def next(self) -> int:
        self.message_id += 1

        return self.message_id

    def add(self, message: Message) -> int:
        """
        message added in order using message.meta.id attribute
        """
        cp = self.copy()
        try:
            self[message.meta.message_id] = message
        except AttributeError:
            raise Exception("Message is not registered!")
        for idx in cp:
            if idx < message.meta.message_id:
                continue
            self.move_to_end(idx)
        return message.meta.message_id

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
        service_id = f"{service.host}:{service.port}"
        self[service_id] = service
        self.servers_number += 1
        self.healthy_servers_number += 1
        return service_id

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





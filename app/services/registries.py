from models.models import Message, SecondaryServer, ServerStatus
import collections


class MessageRegistry(collections.UserDict):
    message_id: int = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        try:
            self[message.meta.message_id] = message
        except AttributeError:
            raise Exception("Message is not registered!")

        return message.meta.message_id

    def __dict__(self) -> dict:
        result = {}
        self._sort()
        for key, value in self.items():
            result[key] = value.dict()
        return result

    def _sort(self):
        for key, value in sorted(self.items(), key=lambda x: x[0], reverse=False):
            self[key] = value


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

    def __dict__(self) -> dict:
        result = {}
        for key, value in self.items():
            result[key] = value.dict()
        return result





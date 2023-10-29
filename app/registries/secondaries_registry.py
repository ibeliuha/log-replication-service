import collections
from models.models import SecondaryServer, ServerStatus


class ServiceRegistry(collections.UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.servers_number: int = 0
        self.healthy_servers_number: int = 0

    def register(self, service: SecondaryServer) -> str:
        if service.id not in self:
            self.servers_number += 1
        self[service.id] = service
        self.healthy_servers_number += 1
        return service.id

    def remove(self, server_id: str):
        self.pop(server_id)
        self.servers_number -= 1
        self.healthy_servers_number -= 1

    def update_status(self, server_id: str, new_status: ServerStatus):
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

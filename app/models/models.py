from pydantic import BaseModel, IPvAnyAddress
from models.item import Item
import enum
from datetime import datetime
from typing import Optional, Dict, Any


class MessageMeta(BaseModel):
    message_id: int
    registered_at: datetime
    registered_to: Optional[set[str]] = set()

    def dict(self, *args, **kwargs):
        res = dict(self)
        res['registered_at'] = str(res['registered_at'])
        res['registered_to'] = list(res['registered_to'])
        return res


class Message(Item):
    meta: Optional[MessageMeta] = None

    def register(self, message_id: int):
        self.meta = MessageMeta(
            message_id=message_id,
            registered_at=datetime.now()
        )
        return self

    def dict(self, *args, **kwargs):
        res = super().dict()
        res['meta'] = self.meta.dict()
        return res

    def __str__(self):
        message_str = f"message: {self.message}"
        if self.meta:
            message_str = f"id:{self.meta.message_id}," \
                          f"registered_at: {self.meta.registered_at}," \
                          f"{message_str}"
        return message_str

    def __repr__(self):
        message_str = f"message: {self.message}"
        if self.meta:
            message_str = f"id:{self.meta.message_id}," \
                          f"registered_at: {self.meta.registered_at}," \
                          f"{message_str}"
        return message_str


class ServiceType(enum.Enum):
    MASTER = 'master'
    SLAVE = 'slave'


class ServerStatus(enum.Enum):
    HEALTHY = 1
    UNREACHABLE = 0


class SecondaryServer(BaseModel):
    id: str
    host: IPvAnyAddress
    port: int
    status: ServerStatus = 1
    last_healthy_status: datetime = datetime.now()

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            'id': self.id,
            'host': str(self.host),
            'port': self.port,
            'status': self.status,
            'last_healthy_status': self.last_healthy_status.strftime('%Y-%m-%d %H:%M:%S')
        }


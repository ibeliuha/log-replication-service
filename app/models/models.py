import enum
from datetime import datetime
from pydantic import BaseModel, IPvAnyAddress
from typing import Optional, Dict, Any
from models.item import Item


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
        res = dict(self)
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
    SECONDARY = 'secondary'


class ServerStatus(enum.Enum):
    HEALTHY = 1
    SUSPECTED = 0
    UNHEALTHY = -1


class SecondaryServer(BaseModel):
    id: str
    host: IPvAnyAddress
    port: int
    status: ServerStatus
    last_status_change: datetime

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            'id': self.id,
            'host': str(self.host),
            'port': self.port,
            'status': self.status.name,
            'last_status_change': self.last_status_change.strftime('%Y-%m-%d %H:%M:%S')
        }
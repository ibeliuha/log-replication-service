from pydantic import BaseModel, IPvAnyAddress
import enum
from datetime import datetime
from typing import Optional, Dict, Any


class MessageMeta(BaseModel):
    message_id: int
    registered_at: datetime
    registered_to: Optional[list[str]]

    def dict(self, *args, **kwargs):
        res = dict(self)
        res['registered_at'] = str(res['registered_at'])
        return res


class Message(BaseModel):
    message: str
    meta: Optional[MessageMeta] = None

    def register(self, message_id: int):
        self.meta = MessageMeta(
            message_id=message_id,
            registered_at=datetime.now(),
            registered_to=[]
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
    SLAVE = 'slave'


class ServerStatus(enum.Enum):
    HEALTHY = 1
    UNREACHABLE = 0


class SecondaryServer(BaseModel):
    host: IPvAnyAddress
    port: int
    status: ServerStatus = 1
    last_healthy_status: datetime = datetime.now()

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            'host': str(self.host),
            'port': self.port,
            'status': self.status,
            'last_healthy_status': self.last_healthy_status.strftime('%Y-%m-%d %H:%M:%S')
        }


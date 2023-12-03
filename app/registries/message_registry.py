from models.models import Message
import collections
from utils.exceptions import MessageDuplicationError


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
        if message.meta.message_id in [*self.awaited_messages, *self]:
            raise MessageDuplicationError(message_id=message.meta.message_id)
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
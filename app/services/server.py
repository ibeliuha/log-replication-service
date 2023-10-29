import asyncio
import os
import httpx
from datetime import datetime
import logging
from utils.exceptions import AuthorizationError, UnexpectedResponse
from utils.handlers import async_handler, sync_handler
from services.registries import MessageRegistry, ServiceRegistry
from models.models import ServiceType, SecondaryServer, Message, ServerStatus
from config import CONFIG
from registries import MESSAGE_REGISTRY, SECONDARIES_REGISTRY


class Server:
    def __init__(self):
        self.service_type: ServiceType = ServiceType(os.getenv('SERVICE_TYPE'))
        self.id = os.getenv('HOSTNAME')

    def start(self):
        raise NotImplementedError("Function is not defined for base class")

    @staticmethod
    async def register_message(**kwargs):
        raise NotImplementedError("Function is not defined for base class")

    @staticmethod
    def get_message_list(api_key) -> MessageRegistry:
        if api_key not in (CONFIG.SERVICE_TOKEN, CONFIG.CLIENT_TOKEN):
            raise AuthorizationError(service='Get Message Registry')
        return MESSAGE_REGISTRY


class Master(Server):
    def __init__(self):
        super().__init__()
        self.conditions = dict()

    def start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._secondaries_healthcheck(
            periodicity=CONFIG.HEALTHCHECK_DELAY,
            remove_after=CONFIG.SECONDARY_REMOVAL_DELAY
        ))

    async def register_service(self, service: SecondaryServer, api_key: str) -> tuple[int, str]:
        if not CONFIG.SERVICE_TOKEN == api_key:
            raise AuthorizationError(service='Secondary Registration')
        service_id = SECONDARIES_REGISTRY.register(service=service)
        loop = asyncio.get_event_loop()
        loop.create_task(self.send_all(service_id=service_id))
        return service_id

    async def send_all(self, service_id: str):
        for item in MESSAGE_REGISTRY.copy():
            await self._publish_to_secondary(message=MESSAGE_REGISTRY[item], service_id=service_id)

    @staticmethod
    def get_secondaries_registry(api_key: str):
        if not CONFIG.CLIENT_TOKEN == api_key:
            raise AuthorizationError(service='Get Secondary Registry')
        return SECONDARIES_REGISTRY

    async def register_message(self, api_key: str, message: Message, wc: int) -> int:
        if not CONFIG.CLIENT_TOKEN == api_key:
            raise AuthorizationError(service='Message Registration')
        message_id = MESSAGE_REGISTRY.register(message)
        MESSAGE_REGISTRY[message_id].meta.registered_to.add(self.id)

        return await self._broadcast(message_id=message_id, wc=wc)

    async def _broadcast(self, message_id: int, wc: int) -> int:
        """
        broadcasting messages to all secondaries
        wait message to deliver to wc(number of secondaries) before response to a client
        """
        condition = asyncio.Condition()
        self.conditions[message_id] = condition
        message = MESSAGE_REGISTRY[message_id]
        loop = asyncio.get_event_loop()
        for service_id, service in SECONDARIES_REGISTRY.items():
            loop.create_task(self._publish_to_secondary(message=message,
                                                        service_id=service_id))
        async with condition:
            await condition.wait_for(lambda: len(message.meta.registered_to) >= wc)
            _ = self.conditions.pop(message_id)
        return message_id

    @async_handler
    async def _publish_to_secondary(self,
                                    message: Message,
                                    service_id: str,
                                    timeout: int = 100):
        service: SecondaryServer = SECONDARIES_REGISTRY[service_id]
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    url=f'http://{service.host}:{service.port}/messages',
                    headers={'x-token': CONFIG.SERVICE_TOKEN},
                    json=message.dict(),
                    timeout=timeout
                )
                response.raise_for_status()
                message.meta.registered_to.add(service_id)
            except httpx.HTTPError:
                raise Exception(f"Message(id: {message.meta.message_id}) wasn't published "
                      f"to Service(host={service.host}, port={service.port})")
            except httpx.ConnectError:
                raise Exception(
                    f"Can't connect to Service(host={service.host}, port={service.port})"
                )
        condition = self.conditions.get(message.meta.message_id)
        if condition:
            async with condition:
                condition.notify()

    @staticmethod
    async def _secondaries_healthcheck(periodicity: int, remove_after: int):
        async def process(client: httpx.AsyncClient, server_id: str):
            server: SecondaryServer = SECONDARIES_REGISTRY[server_id]
            try:
                res = await client.get(f"http://{server.host}:{server.port}/healthcheck")
                res.raise_for_status()
                SECONDARIES_REGISTRY.update_status(server_id=server_id,
                                                   new_status=ServerStatus.HEALTHY)
                # server.last_healthy_status = datetime.now()
            except httpx.HTTPError:
                SECONDARIES_REGISTRY.update_status(server_id=server_id,
                                                   new_status=ServerStatus.SUSPENDED)
                if (datetime.now()-server.last_status_change).seconds >= remove_after:
                    SECONDARIES_REGISTRY.remove(server_id=server_id)
                    logging.getLogger("error").error(
                        f'Secondary server (id={server_id}) was removed due to inactivity')

        while True:
            async with httpx.AsyncClient() as client:
                tasks = [process(client=client, server_id=server_id) for server_id in SECONDARIES_REGISTRY]
                await asyncio.gather(*tasks)
            await asyncio.sleep(periodicity)


class Secondary(Server):
    def __init__(self):
        super().__init__()
        self.is_registered: bool = False

    def start(self):
        self._register_to_master()
        self.is_registered = True

    @sync_handler
    def _register_to_master(self):
        with httpx.Client() as client:
            try:
                response = client.post(
                    url=f"{CONFIG.MASTER_HOST}:{CONFIG.MASTER_PORT}/secondary/register?_id={self.id}",
                    headers={'x-token': CONFIG.SERVICE_TOKEN}
                )
                response.raise_for_status()
            except KeyError:
                raise UnexpectedResponse(service="Registration to master")

    @staticmethod
    async def register_message(api_key: str, message: Message, **kwargs) -> int:
        if not CONFIG.SERVICE_TOKEN == api_key:
            raise AuthorizationError(service="Message Registration")
        MESSAGE_REGISTRY.add(message)

        return message.meta.message_id


import asyncio
import os
from typing import Optional
import httpx
from datetime import datetime
import logging
from utils.exceptions import AuthorizationError, UnexpectedResponse
from utils.handlers import async_handler, sync_handler
from services.registries import MessageRegistry, ServiceRegistry
from models.models import ServiceType, SecondaryServer, Message, ServerStatus
from config import CONFIG


class Server:
    def __init__(self):
        self.service_type: ServiceType = ServiceType(os.getenv('SERVICE_TYPE'))
        self.message_registry: MessageRegistry = MessageRegistry()

    def start(self):
        raise NotImplementedError("Function is not defined for base class")

    async def register_message(self, **kwargs):
        raise NotImplementedError("Function is not defined for base class")

    def get_message_list(self, api_key) -> MessageRegistry:
        if api_key not in (CONFIG.SERVICE_TOKEN, CONFIG.CLIENT_TOKEN):
            raise AuthorizationError(service='Get Message Registry')
        return self.message_registry


class Master(Server):
    def __init__(self):
        super().__init__()
        self.service_registry: ServiceRegistry = ServiceRegistry()

    def start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._secondaries_healthcheck(
            periodicity=CONFIG.HEALTHCHECK_DELAY,
            remove_after=CONFIG.SECONDARY_REMOVAL_DELAY
        ))

    async def register_service(self, service: SecondaryServer, api_key: str) -> tuple[int, str]:
        if not CONFIG.SERVICE_TOKEN == api_key:
            raise AuthorizationError(service='Secondary Registration')
        service_id = self.service_registry.register(service=service)
        loop = asyncio.get_event_loop()
        loop.create_task(self.send_all(service_id=service_id))
        return service_id

    async def send_all(self, service_id: str):
        for item in self.message_registry:
            await self._publish_to_secondary(message=self.message_registry[item], service_id=service_id)

    def get_secondaries_registry(self, api_key: str):
        if not CONFIG.CLIENT_TOKEN == api_key:
            raise AuthorizationError(service='Get Secondary Registry')
        return self.service_registry

    async def register_message(self, api_key: str, message: Message, wc: Optional[int]) -> int:
        """
        wc (write concern) is set to a minimum of (wc, number of registered services)
        """
        if not CONFIG.CLIENT_TOKEN == api_key:
            raise AuthorizationError(service='Message Registration')
        wc = min(self.service_registry.servers_number, (wc or self.service_registry.servers_number))
        message_id = self.message_registry.register(message)

        return await self._broadcast(message_id=message_id, wc=wc)

    async def _broadcast(self, message_id: int, wc: int) -> int:
        """
        broadcasting messages to all secondaries
        wait message to deliver to wc(number of secondaries) before response to a client
        """
        condition = asyncio.Condition()
        message = self.message_registry[message_id]
        loop = asyncio.get_event_loop()
        for service_id, service in self.service_registry.items():
            loop.create_task(self._publish_to_secondary(message=message,
                                                        service_id=service_id,
                                                        condition=condition))
        async with condition:
            await condition.wait_for(lambda: len(message.meta.registered_to) >= wc)
        return message_id

    @async_handler
    async def _publish_to_secondary(self,
                                    message: Message,
                                    service_id: str,
                                    condition: asyncio.Condition,
                                    timeout: int = 100):
        service: SecondaryServer = self.service_registry[service_id]
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    url=f'http://{service.host}:{service.port}/messages',
                    headers={'x-token': CONFIG.SERVICE_TOKEN},
                    json=message.dict(),
                    timeout=timeout
                )
                response.raise_for_status()
            except httpx.HTTPError:
                raise Exception(f"Message(id: {message.meta.message_id}) wasn't published "
                      f"to Service(host={service.host}, port={service.port})")
            except httpx.ConnectError:
                raise Exception(
                    f"Can't connect to Service(host={service.host}, port={service.port})"
                )
        async with condition:
            message.meta.registered_to.add(service_id)
            condition.notify()

    async def _secondaries_healthcheck(self, periodicity: int, remove_after: int):
        async def process(client: httpx.AsyncClient, server_id: str):
            server: SecondaryServer = self.service_registry[server_id]
            try:
                res = await client.get(f"http://{server.host}:{server.port}/healthcheck")
                res.raise_for_status()
                server.status = 1
                server.last_healthy_status = datetime.now()
            except httpx.HTTPError:
                server.status = 0
                if (datetime.now()-server.last_healthy_status).seconds >= remove_after:
                    self.service_registry.remove(server_id=server_id)
                    logging.getLogger("error").error(
                        f'Secondary server (id={server_id}) was removed due to inactivity')
        while True:
            async with httpx.AsyncClient() as client:
                tasks = [process(client=client, server_id=server_id) for server_id in self.service_registry]
                await asyncio.gather(*tasks)
            await asyncio.sleep(periodicity)


class Secondary(Server):
    def __init__(self):
        super().__init__()
        self._id: Optional[int] = None
        self.is_registered: bool = False

    def start(self):
        self._register_to_master()
        self.is_registered = True

    @sync_handler
    def _register_to_master(self):
        with httpx.Client() as client:
            try:
                response = client.post(
                    url=f"{CONFIG.MASTER_HOST}:{CONFIG.MASTER_PORT}/secondary/register?_id={CONFIG.HOSTNAME}",
                    headers={'x-token': CONFIG.SERVICE_TOKEN}
                )
                response.raise_for_status()
                self._id = response.json()['id']
            except KeyError as e:
                raise UnexpectedResponse(service="Registration to master")

    async def register_message(self, api_key: str, message: Message, **kwargs) -> int:
        if not CONFIG.SERVICE_TOKEN == api_key:
            raise AuthorizationError(service="Message Registration")
        self.message_registry.add(message)

        return message.meta.message_id


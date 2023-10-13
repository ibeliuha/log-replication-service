import asyncio
import os
from typing import Optional
import httpx
import time
from services.exceptions import AuthorizationError, UnexpectedResponse
from services.registries import MessageRegistry, TokenRegistry, ServiceRegistry
from models.models import ServiceType, SecondaryServer, Message, ServerStatus
from datetime import datetime


class Server:
    def __init__(self):
        self.token_registry: TokenRegistry = TokenRegistry()
        self.service_type: ServiceType = ServiceType(os.getenv('SERVICE_TYPE'))
        self.message_registry: MessageRegistry = MessageRegistry()

    def get_message_list(self, api_key) -> MessageRegistry:
        if api_key not in (self.token_registry.SERVICE_TOKEN, self.token_registry.CLIENT_TOKEN):
            raise AuthorizationError(service='Message Registry')
        return self.message_registry


class Master(Server):
    def __init__(self):
        super().__init__()
        self.slave_registry: ServiceRegistry = ServiceRegistry()

    def start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._slaves_healthcheck())

    def register_service(self, service: SecondaryServer, api_key: str) -> tuple[int, str]:
        if not self.token_registry.SERVICE_TOKEN == api_key:
            raise AuthorizationError(service='Slave Registration')
        service_id = self.slave_registry.register(service=service)
        return service_id

    async def register_message(self, api_key: str, message: Message, wc: Optional[int]) -> int:
        if not self.token_registry.CLIENT_TOKEN == api_key:
            raise AuthorizationError(service='Message Registration')
        wc = min(self.slave_registry.healthy_servers_number, (wc or self.slave_registry.healthy_servers_number))
        message_id = self.message_registry.register(message)

        return await self._broadcast(message_id=message_id, wc=wc)

    async def _broadcast(self, message_id: int, wc: int) -> int:
        message = self.message_registry[message_id]
        loop = asyncio.get_event_loop()
        for service_id, service in self.slave_registry.items():
            if not service.status:
                continue
            loop.create_task(self._publish_to_secondary(message=message, service_id=service_id))
        return await asyncio.to_thread(self._wait_for_write, message_id=message_id, wc=wc)

    def _wait_for_write(self, message_id: int, wc: int):
        message: Message = self.message_registry[message_id]
        while True:
            if len(message.meta.registered_to) >= wc:
                break
            time.sleep(1/4)
        return message.meta.message_id

    async def _publish_to_secondary(self, message: Message, service_id: int, timeout: int = 100):
        service: SecondaryServer = self.slave_registry[service_id]

        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    url=f'http://{service.host}:{service.port}/messages',
                    headers={'x-token': self.token_registry.SERVICE_TOKEN},
                    json=message.dict(),
                    timeout=timeout
                )
                response.raise_for_status()
                message.meta.registered_to.append(f'{service.host}:{service.port}')
            except httpx.HTTPError as e:
                raise Exception(f"Message(id={message.meta.message_id}) wasn't published "
                      f"to Service(host={service.host}, port={service.port}")
            except httpx.ConnectError:
                raise Exception(
                    f"Can't connect to Service(host={service.host}, port={service.port}"
                )

    def get_slave_registry(self, api_key: str):
        if not self.token_registry.CLIENT_TOKEN == api_key:
            raise AuthorizationError(service='Slave Registry')
        return self.slave_registry

    async def _slaves_healthcheck(self, periodicity: int = 60):
        async def process(client: httpx.AsyncClient, server_id: str):
            server: SecondaryServer = self.slave_registry[server_id]
            try:
                print(f'check {server}')
                res = await client.get(f"http://{server.host}:{server.port}/healthcheck")
                res.raise_for_status()
                server.status = 1
                server.last_healthy_status = datetime.now()
            except httpx.HTTPError:
                server.status = 0
                if (datetime.now()-server.last_healthy_status).seconds >= 300:
                    self.slave_registry.remove(server_id=server_id)
        while True:
            async with httpx.AsyncClient() as client:
                tasks = [process(client=client, server_id=server_id) for server_id in self.slave_registry]
                await asyncio.gather(*tasks)
            await asyncio.sleep(periodicity)


class Slave(Server):
    def __init__(self):
        super().__init__()
        self._id: Optional[int] = None
        self.registered: bool = False

    def start(self):
        self.register_to_master()

    def register_to_master(self,
                           master_url: str = f"{os.getenv('MASTER_HOST')}:{os.getenv('MASTER_PORT')}",
                           attempt: int = 1,
                           max_attempts: int = 3) -> bool:
        if attempt == max_attempts+1:
            raise Exception("Service is not registered")
        with httpx.Client() as client:
            try:
                response = client.post(
                    url=f'{master_url}/slaves/register',
                    headers={'x-token': self.token_registry.SERVICE_TOKEN}
                )
                response.raise_for_status()
                self._id = response.json()['id']
                return self.registered
            except (httpx.ConnectError, httpx.HTTPError):
                time.sleep(60)
                return self.register_to_master(attempt=attempt+1)
            except KeyError:
                raise UnexpectedResponse(service="Registration to master")

    async def register_message(self, api_key: str, message: Message, **kwargs) -> int:
        if not self.token_registry.SERVICE_TOKEN == api_key:
            raise AuthorizationError(service="Message Registration")
        self.message_registry[message.meta.message_id] = message

        return message.meta.message_id

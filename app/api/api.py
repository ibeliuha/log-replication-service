import logging
import os
from datetime import datetime
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.requests import Request
from fastapi import Header, HTTPException
from typing import Optional, Annotated
from services import SERVICE
from config import CONFIG
from models.models import Message, SecondaryServer, ServerStatus
from utils.exceptions import AuthorizationError, MessageDuplicationError, ReadOnlyException
from utils.other import delay
from registries import SECONDARIES_REGISTRY


master_router = APIRouter()
secondary_router = APIRouter()


@master_router.get('/messages', status_code=200)
@secondary_router.get('/messages', status_code=200)
async def get_message_list(x_token: Annotated[str, Header()]):
    try:
        message_registry = SERVICE.get_message_list(api_key=x_token)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    return JSONResponse(
        content={"data": message_registry.list()},
        status_code=200
    )


@master_router.put('/messages', status_code=200)
@secondary_router.put('/messages', status_code=200)
async def post_message(x_token: Annotated[str, Header()],
                       message: Message,
                       wc: Optional[int] = None):
    """
    wc (write concern) default value is set to total registered secondaries + 1 (master)
    if server is secondary, wc parameter is ignored
    """
    await delay(*[int(x) for x in (os.getenv('DELAY', '0,0').split(','))])
    # wc = wc or SECONDARIES_REGISTRY.servers_number+1

    wc = wc or SECONDARIES_REGISTRY.quorum
    if wc <= 0 or wc > SECONDARIES_REGISTRY.servers_number+1:
        raise HTTPException(status_code=400,
                            detail=f'wc parameter is out of range:'
                                   f'accepted range=[1, {SECONDARIES_REGISTRY.servers_number+1}];'
                                   f'given={wc}. '
                                   f'Currently {SECONDARIES_REGISTRY.healthy_servers_number} out of '
                                   f'{SECONDARIES_REGISTRY.servers_number} secondaries are reachable!'
                            )
    try:
        _ = await SERVICE.register_message(
            message=message,
            api_key=x_token,
            wc=wc
        )
    except (AuthorizationError, MessageDuplicationError, ReadOnlyException) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    return JSONResponse(content=message.dict())


@master_router.post('/secondary/register', status_code=200)
async def register_to_master(_id: str, x_token: Annotated[str, Header()], request: Request):
    try:
        service_id = await SERVICE.register_service(
            service=SecondaryServer(
                id=_id,
                host=request.client.host,
                port=CONFIG.SECONDARY_PORT or request.client.port,
                status=ServerStatus.HEALTHY,
                last_status_change=datetime.now()
            ),
            api_key=x_token
        )
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    return JSONResponse(content={
        'id': service_id
    })


@master_router.get('/secondary/list', status_code=200)
async def get_working_secondaries(x_token: Annotated[str, Header()]):
    try:
        registry = SERVICE.get_secondaries_registry(api_key=x_token)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    return JSONResponse(content={"data": registry.list()})


@master_router.get('/healthcheck', status_code=200)
@secondary_router.get('/healthcheck', status_code=200)
def healthcheck():
    return PlainTextResponse('HEALTHY')

import os
import asyncio
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.requests import Request
from fastapi import Header, HTTPException
from pydantic import BaseModel
from typing import Optional, Annotated
import global_entities
from models.models import Message, SecondaryServer
from utils.exceptions import AuthorizationError

master_router = APIRouter()
slave_router = APIRouter()

# route = FastAPI()


class PostQueryParams(BaseModel):
    message: Message
    write_concern: Optional[int] = None


@master_router.get('/messages', status_code=200)
@slave_router.get('/messages', status_code=200)
async def get_message_list(x_token: Annotated[str, Header()]):
    try:
        message_registry = global_entities.SERVICE.get_message_list(api_key=x_token)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    return JSONResponse(
        content=message_registry.__dict__(),
        status_code=200
    )


@master_router.put('/messages', status_code=200)
@slave_router.put('/messages', status_code=200)
async def post_message(x_token: Annotated[str, Header()],
                       message: Message,
                       wc: Optional[int] = None):
    await asyncio.sleep(int(os.getenv('DELAY', 0)))
    try:
        _ = await global_entities.SERVICE.register_message(
            message=message,
            api_key=x_token,
            wc=wc
        )
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    return JSONResponse(content=message.dict())


@master_router.post('/secondary/register', status_code=200)
async def register_to_master(x_token: Annotated[str, Header()], request: Request):
    try:
        service_id = await global_entities.SERVICE.register_service(
            service=SecondaryServer(
                host=request.client.host,
                port=os.getenv('SLAVE_PORT') or request.client.port
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
        registry = global_entities.SERVICE.get_secondaries_registry(api_key=x_token)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    return JSONResponse(content=registry.__dict__())


@master_router.get('/healthcheck', status_code=200)
@slave_router.get('/healthcheck', status_code=200)
def healthcheck():
    return PlainTextResponse('HEALTHY')

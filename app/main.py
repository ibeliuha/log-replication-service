import global_entities
from models.models import ServiceType
from services.server import Master, Slave
from config.config import Config
from fastapi import FastAPI
import os
from api.api import master_router, slave_router


app = FastAPI()


@app.on_event('startup')
def init():
    global app
    global_entities.CONFIG = Config()

    global_entities.SERVICE = {
        ServiceType.MASTER: Master,
        ServiceType.SLAVE: Slave
    }[ServiceType(os.getenv("SERVICE_TYPE"))]()
    global_entities.SERVICE.start()

    app.include_router(router={
        ServiceType.MASTER: master_router,
        ServiceType.SLAVE: slave_router
    }[global_entities.SERVICE.service_type])

# if __name__ == '__main__':
#     os.environ['SERVICE_TYPE'] = sys.argv[2]
#     uvicorn.run(app=app, port=int(sys.argv[1]))

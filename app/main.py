import sys
import uvicorn
import global_entities
from models.models import ServiceType
from services.server import Master, Slave
from fastapi import FastAPI
import os
from api.api import master_router, slave_router


app = FastAPI()


@app.on_event('startup')
def init():
    global app
    # os.environ['API_KEY'] = 'hog32422of24gr5t'
    # os.environ['SERVICE_TYPE'] = 'master'
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
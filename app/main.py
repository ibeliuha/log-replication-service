from services import SERVICE
from models.models import ServiceType
from fastapi import FastAPI
from api.api import master_router, slave_router


app = FastAPI()


@app.on_event('startup')
def init():
    global app
    SERVICE.start()

    app.include_router(router={
        ServiceType.MASTER: master_router,
        ServiceType.SLAVE: slave_router
    }[SERVICE.service_type])

# if __name__ == '__main__':
#     os.environ['SERVICE_TYPE'] = sys.argv[2]
#     uvicorn.run(app=app, port=int(sys.argv[1]))

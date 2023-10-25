import os
from typing import Union
from services.server import Master, Slave
from models.models import ServiceType


SERVICE: Union[Master, Slave] = {
        ServiceType.MASTER: Master,
        ServiceType.SLAVE: Slave
    }[ServiceType(os.getenv("SERVICE_TYPE"))]()

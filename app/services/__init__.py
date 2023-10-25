from services.server import Master, Slave
from models.models import ServiceType
import os
from typing import Union


SERVICE: Union[Master, Slave] = {
        ServiceType.MASTER: Master,
        ServiceType.SLAVE: Slave
    }[ServiceType(os.getenv("SERVICE_TYPE"))]()

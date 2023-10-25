import os
from typing import Union
from services.server import Master, Secondary
from models.models import ServiceType


SERVICE: Union[Master, Secondary] = {
        ServiceType.MASTER: Master,
        ServiceType.SECONDARY: Secondary
    }[ServiceType(os.getenv("SERVICE_TYPE"))]()

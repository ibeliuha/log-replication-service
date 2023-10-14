from services.server import Master, Slave
from services.registries import Config
from typing import Union


SERVICE: Union[Master, Slave]
GLOBAL_CONFIG: Config

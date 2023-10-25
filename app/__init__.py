from services.server import Master, Secondary
from config.config import Config
from typing import Union


SERVICE: Union[Master, Secondary]
CONFIG: Config
import logging
import os
import asyncio
from starlette.websockets import WebSocket
from utils.path import PATHLOG

class WebSocketLogHandler(logging.Handler):
    """
    Un manejador de logs que emite registros a un cliente WebSocket.
    """
    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket
        self.loop = asyncio.get_running_loop()

    def emit(self, record):
        """
        Emite un registro.
        Formatea el registro y lo envía al WebSocket de forma segura entre hilos.
        """
        msg = self.format(record)
        # Programa la corutina send_text en el event loop desde el hilo actual
        asyncio.run_coroutine_threadsafe(
            self.websocket.send_text(msg), self.loop
        )

def setup_migrate_service_logger():
    """
    Configura el logger para migrate_service.
    Se registrará tanto en archivo como en consola.
    """
    logger = logging.getLogger("migrate_service")
    logger.setLevel(logging.INFO)

    # Evitar añadir múltiples handlers si ya existen
    if not logger.handlers:
        file_handler = logging.FileHandler(os.path.join(PATHLOG, "migrate_service.log"))
        file_handler.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger

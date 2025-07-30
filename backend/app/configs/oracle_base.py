import os, logging
import oracledb
from dotenv import load_dotenv
from utils.path import BASEDIR
from middlewares.output_type_handler import output_type_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the environment variables
load_dotenv()

instant_client_path = os.path.join(BASEDIR, "oracle_home", "instantclient")
oracledb.init_oracle_client(lib_dir=instant_client_path)

DB_ORACLE_USER_TRANSACTIONAL = os.getenv("DB_ORACLE_USER_TRANSACTIONAL")
DB_ORACLE_PASSWORD_TRANSACTIONAL = os.getenv("DB_ORACLE_PASSWORD_TRANSACTIONAL")
DB_ORACLE_DSN_TRANSACTIONAL = os.getenv("DB_ORACLE_DSN_TRANSACTIONAL")


def get_oracle_base_connection():
    try:
        oracle_base_connection = oracledb.connect(
            user=DB_ORACLE_USER_TRANSACTIONAL,
            password=DB_ORACLE_PASSWORD_TRANSACTIONAL,
            dsn=DB_ORACLE_DSN_TRANSACTIONAL,
            disable_oob=True
        )
        oracle_base_connection.outputtypehandler = output_type_handler
        return oracle_base_connection
    except oracledb.DatabaseError as e:
        logger.error("Error de base de datos durante la conexión: %s", e)
        raise
    except oracledb.Error as e:
        logger.error("Error de Oracle durante la conexión: %s", e)
        raise
    except Exception as e:
        logger.error("Error genérico durante la conexión: %s", e)
        raise


def get_reconnect_oracle_base(oracle_base_connection):
    try:
        if testing_oracle_base_connection(oracle_base_connection):
            return oracle_base_connection
        else:
            return get_oracle_base_connection()
    except oracledb.DatabaseError as e:
        logger.error("Error de base de datos durante la conexión: %s", e)
        raise
    except oracledb.Error as e:
        logger.error("Error de Oracle durante la conexión: %s", e)
        raise
    except Exception as e:
        logger.error("Error genérico durante la conexión: %s", e)
        raise


def testing_oracle_base_connection(oracle_base_connection) -> bool:
    try:
        if oracle_base_connection is None:
            return False
        oracle_base_connection.outputtypehandler = output_type_handler
        cursor = oracle_base_connection.cursor()
        cursor.execute("SELECT * FROM v$version")
        version = cursor.fetchone()[0]
        cursor.close()
        logger.info("Oracle Server Version: %s", version)
        return True
    except oracledb.DatabaseError as e:
        logger.error("Error de base de datos durante la prueba de conexión: %s", e)
        return False
    except oracledb.Error as e:
        logger.error("Error de Oracle durante la prueba de conexión: %s", e)
        return False
    except Exception as e:
        logger.error("Error genérico durante la prueba de conexión: %s", e)
        return False


class OracleTransaction:
    def __init__(self):
        self.connection = get_oracle_base_connection()

    def __enter__(self):
        self.connection = get_reconnect_oracle_base(self.connection)
        return self.connection

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()
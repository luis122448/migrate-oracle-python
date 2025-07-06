import os, logging
import oracledb
from dotenv import load_dotenv
from middlewares.output_type_handler import output_type_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the environment variables
load_dotenv()

DB_ORACLE_USER_WAREHOUSE = os.getenv("DB_ORACLE_USER_WAREHOUSE")
DB_ORACLE_PASSWORD_WAREHOUSE = os.getenv("DB_ORACLE_PASSWORD_WAREHOUSE")
DB_ORACLE_DSN_WAREHOUSE = os.getenv("DB_ORACLE_DSN_WAREHOUSE")


def get_oracle_warehouse_connection():
    try:
        oracle_warehouse_connection = oracledb.connect(
            user=DB_ORACLE_USER_WAREHOUSE,
            password=DB_ORACLE_PASSWORD_WAREHOUSE,
            dsn=DB_ORACLE_DSN_WAREHOUSE,
            disable_oob=True
        )
        oracle_warehouse_connection.outputtypehandler = output_type_handler
        return oracle_warehouse_connection
    except oracledb.DatabaseError as e:
        logger.error("Error de base de datos durante la conexión: %s", e)
        raise
    except oracledb.Error as e:
        logger.error("Error de Oracle durante la conexión: %s", e)
        raise
    except Exception as e:
        logger.error("Error genérico durante la conexión: %s", e)
        raise


def get_reconnect_oracle_warehouse(oracle_warehouse_connection):
    try:
        if testing_oracle_warehouse_connection(oracle_warehouse_connection):
            return oracle_warehouse_connection
        else:
            return get_oracle_warehouse_connection()
    except oracledb.DatabaseError as e:
        logger.error("Error de base de datos durante la conexión: %s", e)
        raise
    except oracledb.Error as e:
        logger.error("Error de Oracle durante la conexión: %s", e)
        raise
    except Exception as e:
        logger.error("Error genérico durante la conexión: %s", e)
        raise


def testing_oracle_warehouse_connection(oracle_warehouse_connection) -> bool:
    try:
        if oracle_warehouse_connection is None:
            return False
        oracle_warehouse_connection.outputtypehandler = output_type_handler
        cursor = oracle_warehouse_connection.cursor()
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


class OracleWarehouse:
    def __init__(self):
        self.connection = get_oracle_warehouse_connection()
    
    def __enter__(self):
        self.connection = get_reconnect_oracle_warehouse(self.connection)
        return self.connection
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

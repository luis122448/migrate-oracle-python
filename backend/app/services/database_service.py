from schemas.api_response_schema import ApiResponseSchema
from configs.oracle_base import get_oracle_base_connection
from configs.oracle_autonomous import get_oracle_autonomous_connection

class DatabaseService:
    @staticmethod
    def check_oracle_base_connection():
        connection = None
        try:
            connection = get_oracle_base_connection()
            return ApiResponseSchema(status=1, message="Successfully connected to Oracle Base database.")
        except Exception as e:
            return ApiResponseSchema(status=1.2, message=f"Failed to connect to Oracle Base database: {e}")
        finally:
            if connection:
                connection.close()

    @staticmethod
    def check_oracle_autonomous_connection():
        connection = None
        try:
            connection = get_oracle_autonomous_connection()
            return ApiResponseSchema(status=1, message="Successfully connected to Oracle Autonomous database.")
        except Exception as e:
            return ApiResponseSchema(status=1.2, message=f"Failed to connect to Oracle Autonomous database: {e}")
        finally:
            if connection:
                connection.close()

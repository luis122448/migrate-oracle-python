from fastapi import APIRouter, Depends
from services.database_service import DatabaseService
from schemas.api_response_schema import ApiResponseSchema

database_router = APIRouter()

@database_router.get("/check/oracle-base", tags=["DATABASE"], summary="Check Oracle Base Connection", response_model=ApiResponseSchema)
def check_oracle_base(service: DatabaseService = Depends()):
    return service.check_oracle_base_connection()

@database_router.get("/check/oracle-autonomous", tags=["DATABASE"], summary="Check Oracle Autonomous Connection", response_model=ApiResponseSchema)
def check_oracle_autonomous(service: DatabaseService = Depends()):
    return service.check_oracle_autonomous_connection()

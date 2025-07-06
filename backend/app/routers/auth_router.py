import requests
from fastapi import HTTPException, status, APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from auth.auth_handler import JWTBearer
from starlette.responses import JSONResponse
from schemas.auth_schema import BasicAuthSchema, BasicTokenSchema, BasicAnalyticsSchema
from schemas.api_response_schema import ApiResponseAuth
from auth.auth_service import AuthService

auth_router = APIRouter()


@auth_router.get('/auth/test', tags=["AUTH"], response_model=BasicAnalyticsSchema, dependencies=[Depends(JWTBearer())])
def test(token: BasicAnalyticsSchema = Depends(JWTBearer())):
    return token


@auth_router.post('/auth/login', tags=["AUTH"], response_model=ApiResponseAuth)
async def login(auth: BasicAuthSchema, service: AuthService = Depends()):
    try:
        object_response = await service.login(auth)
        return JSONResponse(content=jsonable_encoder(object_response), status_code=status.HTTP_200_OK)
    except Exception as e:
        object_response = ApiResponseAuth(status=1.2, message=str(e), token=None)
        return JSONResponse(content=jsonable_encoder(object_response), status_code=status.HTTP_401_UNAUTHORIZED)

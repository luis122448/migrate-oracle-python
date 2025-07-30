from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middlewares.error_handler import ExceptionHandlerMiddleware, http_exception_handler
from routers.migrate_router import migrate_router
from routers.config_router import config_router
from routers.database_router import database_router
from utils.path import create_dir_logs, get_path_log, get_path_project
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from utils.logger_config import setup_migrate_service_logger

app = FastAPI()

app.title = "App ETL And Analytics API for Oracle Transactional and Oracle Warehouse"
app.version = "1.0.0"
app.description = "ETL And Analytics API"
app.docs_url = "/docs"

# url = "https://sweb3.grupotsiperu.com.pe:8000/docs"

origins = [
    "*"
]


# Add middleware
app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST","DELETE"],
    allow_headers=["*"],
)

# Exception Handler
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# Add routes
app.include_router(migrate_router)
app.include_router(config_router)
app.include_router(database_router)


@app.on_event("startup")
async def startup():
    # Load the environment variables
    load_dotenv()
    print("Startup")
    print('Path Project: ', get_path_project())
    print('Path Log: ', get_path_log())
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('uvicorn')
    logger.setLevel(logging.DEBUG)
    logger.propagate = True
    create_dir_logs()
    setup_migrate_service_logger()


@app.on_event("shutdown")
async def shutdown():
    print("Shutdown")

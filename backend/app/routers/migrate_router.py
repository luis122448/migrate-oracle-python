
import os
from fastapi import status, APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi import BackgroundTasks
from fastapi.encoders import jsonable_encoder
from schemas.api_response_schema import ApiResponseSchema, ApiResponseList
from schemas.migrate_schema import MigrateSchema
from services.migrate_service import MigrateService
import logging
from utils.logger_config import WebSocketLogHandler
from starlette.concurrency import run_in_threadpool
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

migrate_router = APIRouter()

@migrate_router.post('/migrate/all', tags=["MIGRATE"], response_model=ApiResponseSchema)
def migrate_all(
    request_body: MigrateSchema,
    service: MigrateService = Depends()
):
    try:
        object_response = service.migrate_all(
            source_id_cia=request_body.source_id_cia,
            dest_id_cia=request_body.dest_id_cia,
            exceptions=request_body.exceptions,
            run_pre_migration_script=request_body.run_pre_migration_script,
            run_post_migration_script=request_body.run_post_migration_script
        )
        return JSONResponse(content=jsonable_encoder(object_response), status_code=status.HTTP_200_OK)
    except Exception as e:
        object_response = ApiResponseSchema(status=1.2, message=str(e))
        return JSONResponse(content=jsonable_encoder(object_response), status_code=status.HTTP_400_BAD_REQUEST)

@migrate_router.websocket("/migrate/all")
async def websocket_migrate_all(websocket: WebSocket, service: MigrateService = Depends()):
    await websocket.accept()
    handler = WebSocketLogHandler(websocket)
    logger = logging.getLogger("migrate_service")
    logger.addHandler(handler)

    try:
        # Esperar el mensaje inicial del cliente con los parámetros
        data = await websocket.receive_json()
        source_id_cia = data["source_id_cia"]
        dest_id_cia = data["dest_id_cia"]
        exceptions = data.get("exceptions", [])
        run_pre_migration_script = data.get("run_pre_migration_script", True)
        run_post_migration_script = data.get("run_post_migration_script", True)

        # Ejecutar la migración en un hilo para no bloquear el bucle de eventos
        await run_in_threadpool(
            service.migrate_all,
            source_id_cia=source_id_cia,
            dest_id_cia=dest_id_cia,
            exceptions=exceptions,
            run_pre_migration_script=run_pre_migration_script,
            run_post_migration_script=run_post_migration_script
        )
    except WebSocketDisconnect:
        logger.info("Cliente desconectado")
    except Exception as e:
        logger.error(f"Error en la conexión WebSocket: {e}")
    finally:
        logger.removeHandler(handler)
        await websocket.close()

@migrate_router.post('/erp/migrate/report', tags=["MIGRATE"], response_model=ApiResponseSchema)
def validate_migration(request_body: MigrateSchema, service: MigrateService = Depends()):
    try:
        object_response, _ = service.validate_migration(
            source_id_cia=request_body.source_id_cia,
            dest_id_cia=request_body.dest_id_cia,
            exceptions=request_body.exceptions
        )
        return JSONResponse(content=jsonable_encoder(object_response), status_code=status.HTTP_200_OK)
    except Exception as e:
        object_response = ApiResponseSchema(status=1.2, message=str(e))
        return JSONResponse(content=jsonable_encoder(object_response), status_code=status.HTTP_400_BAD_REQUEST)

@migrate_router.post('/erp/migrate/report/pdf', tags=["MIGRATE"])
def validate_migration_pdf(request_body: MigrateSchema, background_tasks: BackgroundTasks, service: MigrateService = Depends()):
    try:
        _, report_lines = service.validate_migration(
            source_id_cia=request_body.source_id_cia,
            dest_id_cia=request_body.dest_id_cia,
            exceptions=request_body.exceptions
        )

        pdf_filename = "migration_report.pdf"
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        width, height = letter

        # Set font to Courier for fixed-width text
        c.setFont("Courier", 10)

        y_position = height - inch # Start from top of the page
        x_position = inch # Left margin
        line_height = 12 # Adjust as needed for spacing

        for line in report_lines:
            sub_lines = line.split('\n')
            for sub_line in sub_lines:
                if not sub_line.strip(): # Skip empty lines after split
                    continue

                if y_position < inch: # Check if we need a new page
                    c.showPage()
                    c.setFont("Courier", 10)
                    y_position = height - inch

                # Handle special formatting for headers and separators
                if sub_line.startswith("MIGRATION VALIDATION REPORT"):
                    c.setFont("Courier-Bold", 12)
                    text_width = c.stringWidth(sub_line, "Courier-Bold", 12)
                    centered_x = (width - text_width) / 2
                    c.drawString(centered_x, y_position, sub_line)
                    c.setFont("Courier", 10) # Reset font
                elif sub_line.startswith("DATA INTEGRITY"):
                    c.setFont("Courier-Bold", 12)
                    text_width = c.stringWidth(sub_line, "Courier-Bold", 12)
                    centered_x = (width - text_width) / 2
                    c.drawString(centered_x, y_position, sub_line)
                    c.setFont("Courier", 10) # Reset font
                elif sub_line.startswith("=") or sub_line.startswith("-"):
                    c.drawString(x_position, y_position, sub_line)
                elif sub_line.startswith("TABLA |"): # Table header
                    c.drawString(x_position, y_position, sub_line)
                else:
                    # For regular lines, just draw them
                    c.drawString(x_position, y_position, sub_line)
                
                y_position -= line_height

        c.save()

        if background_tasks:
            background_tasks.add_task(os.remove, pdf_filename)

        return FileResponse(path=pdf_filename, media_type="application/pdf", filename=pdf_filename)

    except Exception as e:
        object_response = ApiResponseSchema(status=1.2, message=str(e))
        return JSONResponse(content=jsonable_encoder(object_response), status_code=status.HTTP_400_BAD_REQUEST)

@migrate_router.get('/erp/migrate/logs', tags=["MIGRATE"], response_model=ApiResponseList)
def get_migration_logs(log_type: str = None, service: MigrateService = Depends()):
    try:
        logs = service.get_migration_logs(log_type=log_type)
        return JSONResponse(content=jsonable_encoder(ApiResponseList(status=1.0, message="Logs retrieved successfully", list=logs)), status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content=jsonable_encoder(ApiResponseList(status=1.2, message=f"Error retrieving logs: {e}")), status_code=status.HTTP_400_BAD_REQUEST)


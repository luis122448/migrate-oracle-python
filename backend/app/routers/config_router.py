from fastapi import APIRouter, Depends, status
from schemas.config_schema import ConfigAddSchema, ConfigResponseSchema
from services.config_service import ConfigService

config_router = APIRouter()

@config_router.get("/config/tables", response_model=ConfigResponseSchema, tags=["CONFIG"])
def get_tables(service: ConfigService = Depends()):
    """Obtiene la lista actual de tablas a migrar."""
    tables = service.get_tables()
    return ConfigResponseSchema(tables=tables)

@config_router.post("/config/tables", response_model=ConfigResponseSchema, status_code=status.HTTP_201_CREATED, tags=["CONFIG"])
def add_table(request: ConfigAddSchema, service: ConfigService = Depends()):
    """Añade una nueva tabla a la lista de migración."""
    updated_tables = service.add_table(request.table_name)
    return ConfigResponseSchema(message=f"Tabla '{request.table_name}' añadida exitosamente.", tables=updated_tables)

@config_router.delete("/config/tables/{table_name}", response_model=ConfigResponseSchema, tags=["CONFIG"])
def delete_table(table_name: str, service: ConfigService = Depends()):
    """Elimina una tabla de la lista de migración."""
    updated_tables = service.delete_table(table_name)
    return ConfigResponseSchema(message=f"Tabla '{table_name}' eliminada exitosamente.", tables=updated_tables)

@config_router.delete("/config/tables", response_model=ConfigResponseSchema, tags=["CONFIG"])
def delete_all_tables(service: ConfigService = Depends()):
    """Elimina todas las tablas de la configuración."""
    service.delete_all_tables()
    return ConfigResponseSchema(message="Todas las tablas han sido eliminadas.", tables=[])

@config_router.post("/config/restore", response_model=ConfigResponseSchema, tags=["CONFIG"])
def restore_tables(service: ConfigService = Depends()):
    """Restaura la configuración de tablas desde el archivo de respaldo."""
    restored_tables = service.restore_tables()
    return ConfigResponseSchema(message="La configuración de tablas ha sido restaurada.", tables=restored_tables)

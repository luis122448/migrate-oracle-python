from pydantic import BaseModel, Field
from typing import List

class ConfigAddSchema(BaseModel):
    table_name: str = Field(..., description="Nombre de la tabla a añadir")

class ConfigResponseSchema(BaseModel):
    message: str = Field(default="Operación exitosa")
    tables: List[str] = Field(description="Lista de tablas configuradas")

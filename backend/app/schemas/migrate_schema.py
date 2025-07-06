from pydantic import BaseModel
from typing import List, Optional

class MigrateSchema(BaseModel):
    source_id_cia: int
    dest_id_cia: int
    exceptions: Optional[List[str]] = []

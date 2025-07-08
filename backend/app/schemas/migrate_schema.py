from pydantic import BaseModel
from typing import List, Optional

class MigrateSchema(BaseModel):
    source_id_cia: int
    dest_id_cia: int
    exceptions: Optional[List[str]] = []
    run_pre_migration_script: Optional[bool] = True
    run_post_migration_script: Optional[bool] = True


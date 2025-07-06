import os
from fastapi import HTTPException
from utils.path import PATHUTILS

TABLES_FILE = os.path.join(PATHUTILS, "tables.txt")
BACKUP_FILE = os.path.join(PATHUTILS, "tables_backup.txt")

class ConfigService:
    """
    Servicio para gestionar la configuración de las tablas a migrar.
    """

    def get_tables(self) -> list[str]:
        """Lee y devuelve la lista de tablas desde tables.txt."""
        try:
            with open(TABLES_FILE, "r") as f:
                # Filtra líneas vacías y quita espacios en blanco
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            # Si el archivo no existe, lo crea vacío
            open(TABLES_FILE, 'w').close()
            return []
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al leer el archivo de tablas: {e}")

    def _write_tables(self, tables: list[str], sort_tables: bool = True):
        """Escribe la lista de tablas en el archivo, asegurando mayúsculas y sin duplicados. Opcionalmente, las ordena."""
        # Convierte todo a mayúsculas y elimina duplicados, manteniendo el orden de inserción si no se ordena.
        seen = set()
        unique_upper_tables = []
        for t in tables:
            if t.strip() and t.upper() not in seen:
                unique_upper_tables.append(t.upper())
                seen.add(t.upper())

        if sort_tables:
            unique_upper_tables = sorted(unique_upper_tables)

        try:
            with open(TABLES_FILE, "w") as f:
                f.write("\n".join(unique_upper_tables))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al escribir en el archivo de tablas: {e}")
        return unique_upper_tables

    def add_table(self, table_name: str) -> list[str]:
        """Añade una nueva tabla a la lista si no existe."""
        tables = self.get_tables()
        if table_name.upper() in [t.upper() for t in tables]:
            raise HTTPException(status_code=400, detail=f"La tabla '{table_name}' ya existe en la lista.")
        
        tables.append(table_name)
        return self._write_tables(tables)

    def delete_table(self, table_name: str) -> list[str]:
        """Elimina una tabla de la lista."""
        tables = self.get_tables()
        table_to_delete = table_name.upper()
        if table_to_delete not in [t.upper() for t in tables]:
            raise HTTPException(status_code=404, detail=f"La tabla '{table_name}' no se encontró en la lista.")

        new_tables = [t for t in tables if t.upper() != table_to_delete]
        return self._write_tables(new_tables)

    def delete_all_tables(self) -> list[str]:
        """Elimina todas las tablas del archivo."""
        return self._write_tables([])

    def restore_tables(self) -> list[str]:
        """Restaura la lista de tablas desde el archivo de respaldo."""
        try:
            with open(BACKUP_FILE, "r") as backup_f:
                tables = [line.strip() for line in backup_f if line.strip()]
            return self._write_tables(tables)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="No se encontró el archivo de respaldo (tables_backup.txt).")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al restaurar la configuración: {e}")

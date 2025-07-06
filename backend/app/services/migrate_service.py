import oracledb
import time
import os
from datetime import datetime
import locale
import glob
from fastapi import Depends, HTTPException
from schemas.api_response_schema import ApiResponseSchema
from configs.oracle_transactional import OracleTransaction
from configs.oracle_warehouse import OracleWarehouse
from utils.path import PATHLOG, PATHUTILS
from utils.logger_config import setup_migrate_service_logger

# Configuración de logs: se registrará tanto en archivo como en consola.
logger = setup_migrate_service_logger()


class MigrateService:
    """
    Servicio para migrar datos desde Oracle Transactional (origen) hacia Oracle Warehouse (destino)
    en bloques de 1000 registros, filtrando por id_cia (valor origen y destino pueden diferir),
    deshabilitando los triggers en la tabla destino durante la inserción, y generando logs detallados.
    """

    def __init__(self,
                 oracle_transactional: OracleTransaction = Depends(),
                 oracle_warehouse: OracleWarehouse = Depends()) -> None:
        self.oracle_transactional = oracle_transactional
        self.oracle_warehouse = oracle_warehouse
        self.src_conn = self.oracle_transactional.connection
        self.dst_conn = self.oracle_warehouse.connection
        self.src_cursor = self.src_conn.cursor()
        self.dst_cursor = self.dst_conn.cursor()

    def disable_triggers(self, table: str):
        """Deshabilita los triggers en la tabla destino."""
        try:
            query = f"ALTER TABLE {table} DISABLE ALL TRIGGERS"
            self.dst_cursor.execute(query)
            self.dst_conn.commit()
        except Exception as e:
            logger.error(f"Error al deshabilitar triggers en {table}: {e}")

    def enable_triggers(self, table: str):
        """Habilita los triggers en la tabla destino."""
        try:
            query = f"ALTER TABLE {table} ENABLE ALL TRIGGERS"
            self.dst_cursor.execute(query)
            self.dst_conn.commit()
        except Exception as e:
            logger.error(f"Error al habilitar triggers en {table}: {e}")

    def disable_all_triggers_global(self):
        plsql = """
        BEGIN
        FOR rec IN (SELECT trigger_name FROM user_triggers) LOOP
            EXECUTE IMMEDIATE 'ALTER TRIGGER ' || rec.trigger_name || ' DISABLE';
        END LOOP;
        END;
        """
        self.dst_cursor.execute(plsql)
        self.dst_conn.commit()

    def enable_all_triggers_global(self):
        plsql = """
        BEGIN
        FOR rec IN (SELECT trigger_name FROM user_triggers) LOOP
            EXECUTE IMMEDIATE 'ALTER TRIGGER ' || rec.trigger_name || ' ENABLE';
        END LOOP;
        END;
        """
        self.dst_cursor.execute(plsql)
        self.dst_conn.commit()

    def migrate_table(self, table: str, source_id_cia: int, dest_id_cia: int, exceptions: list[str]) -> tuple[int, str]:
        """
        Migra la tabla indicada:
        - Si la tabla no es excepción, se filtran los registros por source_id_cia.
        - En cada lote (10000 registros) se actualiza la columna ID_CIA al valor dest_id_cia.
        - Se consulta la metadata de la tabla destino (ordenada por COLUMN_ID) para conocer los tipos de columnas.
        - Para columnas de tipo VARCHAR/CHAR, se convierten a cadena los valores numéricos.
        - Se utiliza setinputsizes() para forzar los tipos en la inserción y evitar que, al haber NULL, se infiera un tamaño incorrecto.
        - Se registran logs detallados de cada lote insertado.
        Retorna una tupla con el total de registros migrados y una cadena con los errores ocurridos (si los hay).
        """
        total_records = 0
        error_messages = ""
        
        # Cursors locales para la operación en cada tabla.
        src_cur = self.src_conn.cursor()
        dst_cur = self.dst_conn.cursor()

        # Intentar deshabilitar los triggers de la tabla; si falla, se aborta la migración para esta tabla.
        try:
            self.disable_triggers(table)
        except Exception as e:
            error_msg = f"Error al deshabilitar triggers en {table}: {e}"
            logger.error(error_msg)
            # No continuar con la migración de esta tabla.
            src_cur.close()
            dst_cur.close()
            return 0, error_msg

        try:
            if table in exceptions:
                src_query = f"SELECT * FROM {table}"
                src_cur.execute(src_query)
            else:
                src_query = f"SELECT * FROM {table} WHERE ID_CIA = :pin_id_cia"
                src_cur.execute(src_query, pin_id_cia=source_id_cia)

            # Obtener nombre de columnas de la fuente (el orden ya está definido en la consulta)
            columns = [col[0] for col in src_cur.description]
            placeholders = ", ".join([f":{i+1}" for i in range(len(columns))])
            col_names = ", ".join(columns)
            insert_query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"

            # Si la tabla no es excepción, se reemplaza el valor de ID_CIA.
            update_id_cia = (table not in exceptions) and ("ID_CIA" in columns)
            id_cia_index = columns.index("ID_CIA") if update_id_cia else None

            # Obtener la metadata de la tabla destino, ordenada por COLUMN_ID.
            dst_cur.execute(
                f"SELECT column_name, data_type FROM user_tab_columns WHERE table_name = '{table.upper()}' ORDER BY column_id"
            )
            from collections import OrderedDict
            col_types = OrderedDict()
            for row in dst_cur.fetchall():
                col_types[row[0].upper()] = row[1].upper()

            while True:
                batch = src_cur.fetchmany(10000)
                if not batch:
                    break

                # Convertir tuplas a lista para poder modificarlas.
                batch = [list(row) for row in batch]

                if update_id_cia:
                    for row in batch:
                        row[id_cia_index] = dest_id_cia

                # Convertir, para cada columna de tipo VARCHAR/CHAR en destino,
                # los valores que sean int a str.
                for i, row in enumerate(batch):
                    for idx, col in enumerate(columns):
                        col_key = col.upper()
                        if col_key in col_types and col_types[col_key] in ('VARCHAR2', 'CHAR'):
                            if isinstance(row[idx], int):
                                row[idx] = str(row[idx])

                # Definir explícitamente los tipos de entrada para evitar problemas con NULL
                try:
                    input_sizes = []
                    for col in columns:
                        col_key = col.upper()
                        if col_key in col_types:
                            dtype = col_types[col_key]
                            if dtype == 'NUMBER':
                                input_sizes.append(oracledb.DB_TYPE_NUMBER)
                            elif dtype in ('VARCHAR2', 'CHAR'):
                                input_sizes.append(oracledb.DB_TYPE_VARCHAR)
                            elif dtype.startswith('TIMESTAMP'):
                                input_sizes.append(oracledb.DB_TYPE_TIMESTAMP)
                            else:
                                input_sizes.append(None)
                        else:
                            input_sizes.append(None)
                    dst_cur.setinputsizes(*input_sizes)
                except Exception as e:
                    logger.error(f"Error en setinputsizes para {table}: {e}")

                try:
                    dst_cur.executemany(insert_query, batch)
                    self.dst_conn.commit()
                    batch_count = len(batch)
                    total_records += batch_count
                except Exception as e:
                    error_msg = f"Error al insertar lote en {table}: {e}"
                    logger.error(error_msg)
                    error_messages += error_msg + "\n"
                    self.dst_conn.rollback()
        except Exception as e:
            error_msg = f"Error durante la migración de {table}: {e}"
            logger.error(error_msg)
            error_messages += error_msg + "\n"
        finally:
            src_cur.close()
            dst_cur.close()
            try:
                self.enable_triggers(table)
            except Exception as e:
                logger.error(f"Error al habilitar triggers en {table}: {e}")

        return total_records, error_messages

    def migrate_all(self, source_id_cia: int, dest_id_cia: int, exceptions: list[str] = []) -> ApiResponseSchema:
        """
        Realiza la migración de todas las tablas listadas en el archivo 'tables.txt'.
        Se espera que el archivo contenga un nombre de tabla por línea.
        Se deshabilitan y habilitan los triggers de forma masiva para optimizar el proceso.
        Se propagan los errores al archivo de log.
        """
        response = ApiResponseSchema(status=1, message="OK", id_cia=dest_id_cia, timestamp="")
        start_time = time.time()
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        log_filename = f"LOG-{timestamp.replace('/', '-').replace(':', '-')}.txt"
        log_path = os.path.join(PATHLOG, log_filename)

        try:
            with open(os.path.join(PATHUTILS, "tables.txt"), "r") as file:
                tables = [line.strip() for line in file if line.strip()]
        except Exception as e:
            logger.error(f"❌ Error al leer el archivo de tablas: {e}")
            raise HTTPException(status_code=500, detail="Error al leer el archivo de tablas.")

        total_tables = len(tables)
        successful_migrations = 0
        failed_migrations = 0

        # self.disable_all_triggers_global()
        log_entries = []
        log_entries.append(f"📌 INICIO DE MIGRACIÓN - {timestamp}\n")
        log_entries.append(f"Source Company ID: {source_id_cia}\n")
        log_entries.append(f"Destination Company ID: {dest_id_cia}\n")
        log_entries.append("=" * 60 + "\n")

        for table in tables:
            start_table_time = time.time()
            total_records, errors = self.migrate_table(table, source_id_cia, dest_id_cia, exceptions)
            duration = round(time.time() - start_table_time, 2)

            log_entry = f"📂 Tabla: {table}\n"
            log_entry += f"   ⏳ Duración: {duration} seg\n"

            if total_records == 0:
                log_entry += "   ✅ OK: No hay registros para migrar\n"
            else:
                log_entry += f"   ✅ OK: Registros migrados: {total_records}\n"

            if errors:
                log_entry += f"   ❌ ERROR: {errors}\n"
                failed_migrations += 1
            else:
                successful_migrations += 1

            log_entry += "-" * 60 + "\n"            
            log_entries.append(log_entry)            
            logger.info(log_entry.strip())        
            
        # self.enable_all_triggers_global()        
        elapsed_time = round(time.time() - start_time, 2)        
        minutes = int(elapsed_time // 60)
        seconds = round(elapsed_time % 60, 2)
        summary = (
            "\nRESUMEN FINAL\n"
            + "=" * 60 + "\n"
            + f"✅ Tablas migradas exitosamente: {successful_migrations}/{total_tables}\n"
            + f"⚠️ Tablas con errores: {failed_migrations}\n"
            + f"⏳ Tiempo total: {minutes} min {seconds} seg.\n"
            + "=" * 60 + "\n"
        )

        log_entries.append(summary)

        try:
            with open(log_path, "w", encoding="utf-8") as log_file:
                log_file.writelines(log_entries)
            logger.info(f"📄 Reporte de migración generado: {log_path}")
        except Exception as e:
            logger.error(f"❌ Error al escribir el reporte de migración: {e}")

        response.message = f"Proceso finalizado, {successful_migrations}/{total_tables} tablas migradas."
        response.timestamp = f"Finalizado en {minutes} min {seconds} seg."
        logger.info(response.message + " " + response.timestamp)

        return response

    def validate_migration(self, source_id_cia: int, dest_id_cia: int, exceptions: list[str] = []) -> ApiResponseSchema:
        response = ApiResponseSchema(status=1, message="OK", id_cia=dest_id_cia, timestamp="")
        start_time = time.time()
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        timestamp_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        report_filename = f"VALIDATE {timestamp_str}.txt"
        report_path = os.path.join("./logs", report_filename)

        try:
            with open(os.path.join(PATHUTILS, "tables.txt"), "r") as file:
                tables = [line.strip() for line in file if line.strip()]
        except Exception as e:
            logger.error(f"Error al leer el archivo de tablas: {e}")
            raise HTTPException(status_code=500, detail="Error al leer el archivo de tablas.")
        
        max_table_width = max((len(table) for table in tables), default=40)
        table_col_width = max(40, max_table_width + 2)

        header = f"{'TABLE':<{table_col_width}} | {'SOURCE':<8} | {'DESTINA.':<8} | {'DIFFERE.':<8} | STATUS\n"
        separator = "-" * (table_col_width + 42) + "\n"

        report_lines = []
        report_lines.append(f"MIGRATION VALIDATION REPORT - {timestamp}\n")
        report_lines.append("=" * (table_col_width + 42) + "\n")
        report_lines.append(header)
        report_lines.append(separator)

        print("\n🔎 Iniciando validación de migración...\n")
        for table in tables:
            try:
                src_cur = self.src_conn.cursor()
                dst_cur = self.dst_conn.cursor()
                
                if table in exceptions:
                    src_query = f"SELECT COUNT(*) FROM {table}"
                    dst_query = f"SELECT COUNT(*) FROM {table}"
                else:
                    src_query = f"SELECT COUNT(*) FROM {table} WHERE ID_CIA = :pin_id_cia"
                    dst_query = f"SELECT COUNT(*) FROM {table} WHERE ID_CIA = :pin_id_cia"

                src_cur.execute(src_query, pin_id_cia=source_id_cia)
                dst_cur.execute(dst_query, pin_id_cia=dest_id_cia)
                count_src = src_cur.fetchone()[0]
                count_dst = dst_cur.fetchone()[0]
                diff = count_src - count_dst
                
                status = "OK" if diff == 0 else "DIFERENCIA"
                line = f"{table:<{table_col_width}} | {count_src:<8} | {count_dst:<8} | {diff:<8} | {status}"
                report_lines.append(line + "\n")
                print(line)
                
                src_cur.close()
                dst_cur.close()
            except Exception as e:
                error_line = f"{table:<{table_col_width}} | {'ERROR':<8} | {'ERROR':<8} | {'-':<8} | ERROR: {e}"
                logger.error(f"Error al obtener count de {table}: {e}")
                report_lines.append(error_line + "\n")
                print(error_line)

        report_lines.append("\n\n\nDATA INTEGRITY\n")
        report_lines.append("=" * 82 + "\n")
        
        sum_validations = {
            "DOCUMENTOS_CAB": ["PREVEN", "MONAFE", "MONINA", "MONIGV"],
            "DOCUMENTOS_DET": ["CANTID"],
            "DCTA100": ["IMPORTE", "IMPORTEMN", "IMPORTEME"],
            "COMPR010": ["IMPOR01", "IMPOR02"],
            "PROV100": ["IMPORTEMN", "IMPORTEME"],
            "MOVIMIENTOS": ["DEBE01", "DEBE02", "HABER01", "HABER02"],
            "KARDEX": ["COSTOT01", "COSTOT02"],
            "KARDEX001": ["INGRESO", "SALIDA"],
        }
        
        for table, columns in sum_validations.items():
            try:
                src_cur = self.src_conn.cursor()
                dst_cur = self.dst_conn.cursor()
                
                # Construir las consultas aplicando ROUND a 2 decimales para cada columna
                sum_queries = [f"ROUND(NVL(SUM(NVL({col}, 0)),0), 2)" for col in columns]
                query_src = f"SELECT {', '.join(sum_queries)} FROM {table} WHERE ID_CIA = :1"
                query_dst = f"SELECT {', '.join(sum_queries)} FROM {table} WHERE ID_CIA = :1"
                
                src_cur.execute(query_src, (source_id_cia,))
                dst_cur.execute(query_dst, (dest_id_cia,))
                
                sum_src = src_cur.fetchone()
                sum_dst = dst_cur.fetchone()
                
                # Calcular diferencia para cada columna y redondear a 2 decimales
                sum_diff = [round(src - dst, 2) for src, dst in zip(sum_src, sum_dst)] 
                status = "OK" if all(diff == 0 for diff in sum_diff) else "DIFF"
                
                report_lines.append(f"Tabla: {table}\n")
                for col, src, dst, diff in zip(columns, sum_src, sum_dst, sum_diff):
                    report_lines.append(f"  {col:<12}: Origen = {src:<12} | Destino = {dst:<12} | Dif = {diff:<12}\n")
                report_lines.append(f"  ESTADO: {status}\n")
                report_lines.append("-" * 82 + "\n")
                
                # Mostrar en consola el avance en un formato similar
                print(f"\nTabla: {table}")
                for col, src, dst, diff in zip(columns, sum_src, sum_dst, sum_diff):
                    print(f"  {col:<12}: Origen = {src:<12} | Destino = {dst:<12} | Dif = {diff:<12}")
                print(f"  ESTADO: {status}\n")
                
                src_cur.close()
                dst_cur.close()
            except Exception as e:
                logger.error(f"Error al obtener sumas de {table}: {e}")
                report_lines.append(f"ERROR EN {table}: {e}\n")
                print(f"ERROR EN {table}: {e}\n")
        
        with open(report_path, "w", encoding="utf-8") as rpt:
            rpt.writelines(report_lines)
        
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = round(elapsed_time % 60, 2)
        response.message = f"Validación completada. Reporte generado: {report_filename}"
        response.timestamp = f"Finalizado en {minutes} min {seconds} seg."

        print("\n" + "=" * (table_col_width + 42))
        print(response.message)
        print(response.timestamp)
        return response, report_lines

    def get_migration_logs(self, log_type: str = None) -> list[dict]:
        """
        Obtiene una lista de todos los archivos de log de migración y validación,
        incluyendo su nombre y contenido. Puede filtrar por tipo de log.
        """
        log_files_data = []
        log_dir = PATHLOG  # Asumiendo que PATHLOG apunta a la carpeta de logs

        log_patterns = []
        if log_type == "migration":
            log_patterns.append(os.path.join(log_dir, "LOG *.txt"))
        elif log_type == "validation":
            log_patterns.append(os.path.join(log_dir, "VALIDATE *.txt"))
        else:
            # Si no se especifica tipo o es inválido, obtener ambos
            log_patterns.append(os.path.join(log_dir, "LOG *.txt"))
            log_patterns.append(os.path.join(log_dir, "VALIDATE *.txt"))

        for pattern in log_patterns:
            for filepath in glob.glob(pattern):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    log_files_data.append({
                        "filename": os.path.basename(filepath),
                        "content": content
                    })
                except Exception as e:
                    logger.error(f"Error al leer el archivo de log {filepath}: {e}")
                    log_files_data.append({
                        "filename": os.path.basename(filepath),
                        "content": f"Error al leer el archivo: {e}"
                    })
        return log_files_data
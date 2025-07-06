import oracledb

def output_type_handler(cursor, name, defaultType, size, precision, scale):
    if defaultType == oracledb.DB_TYPE_VARCHAR:
        return cursor.var(str, size, arraysize=cursor.arraysize)

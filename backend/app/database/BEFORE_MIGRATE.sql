DELETE FROM usuarios_propiedades p
WHERE
        p.id_cia = PID_CIA
    AND NOT EXISTS (
        SELECT
            1
        FROM
            usuarios u
        WHERE
                u.id_cia = p.id_cia
            AND u.coduser = p.coduser
    );

DELETE FROM permisos p
WHERE
        p.id_cia = PID_CIA
    AND NOT EXISTS (
        SELECT
            1
        FROM
            usuarios u
        WHERE
                u.id_cia = p.id_cia
            AND u.coduser = p.coduser
    );

UPDATE movimientos_conciliacion
SET
    cuenta = 'ND'
WHERE
        id_cia = PID_CIA
    AND TRIM(cuenta) IS NULL;

INSERT INTO empresa_modulos (
   id_cia,
   codmod,
   swacti,
   ucreac,
   uactua,
   fcreac,
   factua
)
   (
      SELECT DISTINCT
            p.id_cia,
            p.codmod,
            'S',
            'admin',
            'admin',
            current_timestamp,
            current_timestamp
      FROM
            permisos p
      WHERE
               p.id_cia = PID_CIA
            AND NOT EXISTS (
               SELECT
                  1
               FROM
                  empresa_modulos um
               WHERE
                        um.id_cia = p.id_cia
                  AND um.codmod = p.codmod
            )
   );

INSERT INTO usuario_modulos (
   id_cia,
   codmod,
   coduser,
   swacti,
   ucreac,
   uactua,
   fcreac,
   factua
)
   (
      SELECT DISTINCT
            p.id_cia,
            p.codmod,
            p.coduser,
            'S',
            'admin',
            'admin',
            current_timestamp,
            current_timestamp
      FROM
            permisos p
      WHERE
               p.id_cia = PID_CIA
            AND NOT EXISTS (
               SELECT
                  1
               FROM
                  usuario_modulos um
               WHERE
                        um.id_cia = p.id_cia
                  AND um.codmod = p.codmod
                  AND um.coduser = p.coduser
            )
   );
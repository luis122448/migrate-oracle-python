INSERT INTO asienhea (
   id_cia,
   periodo,
   mes,
   libro,
   asiento,
   concep
)
   (
      SELECT DISTINCT
            m.id_cia,
            m.periodo,
            m.mes,
            m.libro,
            m.asiento,
            'ASIENTO POR ELIMINADO POR REGULARIZAR'
      FROM
            movimientos m
      WHERE
               m.id_cia = PIN_ID_CIA
            AND NOT EXISTS (
               SELECT
                  1
               FROM
                  asienhea a
               WHERE
                        a.id_cia = m.id_cia
                  AND a.periodo = m.periodo
                  AND a.mes = m.mes
                  AND a.libro = m.libro
                  AND a.asiento = m.asiento
            )
   )
/
DELETE FROM cliente_clase cc
WHERE
        cc.id_cia = PIN_ID_CIA
    AND NOT EXISTS (
        SELECT
            1
        FROM
            cliente cc1
        WHERE
                cc1.id_cia = cc.id_cia
            AND cc1.codcli = cc.codcli
    )
/
DELETE FROM cliente_codpag cc
WHERE
        cc.id_cia = PIN_ID_CIA
    AND NOT EXISTS (
        SELECT
            1
        FROM
            cliente cc1
        WHERE
                cc1.id_cia = cc.id_cia
            AND cc1.codcli = cc.codcli
    )
/
DELETE FROM clientecontacto_clase cc
WHERE
        cc.id_cia = PIN_ID_CIA
    AND NOT EXISTS (
        SELECT
            1
        FROM
            contacto c
        WHERE
                c.id_cia = cc.id_cia
            AND c.codcont = cc.codcont
    )
/
UPDATE asiendet
SET 
    moneda = 'PEN'
WHERE
    id_cia = PIN_ID_CIA
    AND moneda IS NULL
/
UPDATE movimientos
SET 
    moneda = 'PEN'
WHERE
    id_cia = PIN_ID_CIA
    AND moneda IS NULL
/
UPDATE compr010
SET
    concep = 'SIN CONCEPTO'
WHERE
    id_cia = PIN_ID_CIA
    AND concep IS NULL
/
UPDATE prov105
SET
    series = '999'
WHERE
    id_cia = PIN_ID_CIA
    AND series IS NULL
/
INSERT INTO cliente (
   id_cia,
   codcli,
   razonc
)
   (
      SELECT
            cc.id_cia,
            cc.codpro,
            cc.razon
      FROM
            compr010 cc
      WHERE
               cc.id_cia = PIN_ID_CIA
            AND NOT EXISTS (
               SELECT
                  1
               FROM
                  cliente cc1
               WHERE
                        cc1.id_cia = cc.id_cia
                  AND cc1.codcli = cc.codpro
            )
   )
/
INSERT INTO cliente (
    id_cia,
    codcli,
    razonc
)
    (
        SELECT
            cc.id_cia,
            cc.codcli,
            'PROVEEDOR ELIMINADO'
        FROM
            prov105 cc
        WHERE
                cc.id_cia = PIN_ID_CIA
            AND NOT EXISTS (
                SELECT
                    1
                FROM
                    cliente cc1
                WHERE
                        cc1.id_cia = cc.id_cia
                    AND cc1.codcli = cc.codcli
            )
    )
/
DELETE FROM usuarios_propiedades p
WHERE
        p.id_cia = PIN_ID_CIA
    AND NOT EXISTS (
        SELECT
            1
        FROM
            usuarios u
        WHERE
                u.id_cia = p.id_cia
            AND u.coduser = p.coduser
    )
/
DELETE FROM permisos p
WHERE
        p.id_cia = PIN_ID_CIA
    AND NOT EXISTS (
        SELECT
            1
        FROM
            usuarios u
        WHERE
                u.id_cia = p.id_cia
            AND u.coduser = p.coduser
    )
/
UPDATE movimientos_conciliacion
SET
    cuenta = 'ND'
WHERE
        id_cia = PIN_ID_CIA
    AND TRIM(cuenta) IS NULL
/
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
               p.id_cia = PIN_ID_CIA
            AND NOT EXISTS (
               SELECT
                  1
               FROM
                  empresa_modulos um
               WHERE
                        um.id_cia = p.id_cia
                  AND um.codmod = p.codmod
            )
   )
/
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
               p.id_cia = PIN_ID_CIA
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
   )
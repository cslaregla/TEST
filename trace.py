import pandas as pd
import hashlib, random, re
from datetime import datetime, timedelta, time as dtime
from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg://postgres:test@localhost:5433/postgres")

MAPA_COLUMNAS = {
    "NRO": "nro_legado", "ID": "id_legado", "FECHA Y HORA": "fecha_hora",
    "OPERADOR": "operador", "CANAL DE INGRESO": "canal_ingreso",
    "TIPO DE RECURRENTE": "tipo_recurrente", "AREA DEL RECURRENTE": "area_recurrente",
    "NOMBRE DEL RECURRENTE": "nombre_recurrente", "TELEFONO DEL RECURRENTE": "telefono_recurrente",
    "DESCRIPCIÓN DEL PROCEDIMIENTO": "descripcion", "CATEGORÍA": "categoria",
    "TIPO DE PROCEDIMIENTO": "tipo_procedimiento", "CALLE": "calle",
    "NUMERACIÓN": "numeracion", "CALLE QUE INTERSECTA": "calle_interseccion",
    "LUGAR PÚBLICO/PRIVADO": "lugar_tipo", "ACLARATORIA DE LA UBICACIÓN": "aclaratoria_ubicacion",
    "CUADRANTE": "cuadrante", "RADIOPERADOR": "radiooperador", "NRO DE MOVIL": "movil",
    "INSPECTOR ASIGNADO": "inspector", "ESTADO DEL PROCEDIMIENTO": "estado",
    "HORA DE ASIGNACIÓN": "hora_asignacion_raw", "HORA DE ARRIBO": "hora_arribo_raw",
    "HORA DE TERMINO": "hora_termino_raw", "INFORME": "informe",
    "FINALIZACIÓN": "finalizacion", "APOYO/ASISTENCIA": "apoyo_asistencia",
    "COMISARIA": "comisaria", "SEREMI": "seremi",
    "DERIVACIÓN A OTRA COMUNA": "derivacion_comuna", "OBSERVACIONES": "observaciones",
    "CONNOTACIÓN": "connotacion", "COORDENADAS": "coordenadas",
}

df_crudo = pd.read_csv("test.csv", sep=';', engine='python',keep_default_na=False)
df_crudo = df_crudo.fillna("").astype(str) 

# Diagnóstico: si algo sale aquí, ajusta MAPA_COLUMNAS con el nombre real
faltantes = set(MAPA_COLUMNAS) - set(df_crudo.columns)
if faltantes:
    print("⚠️ No encontré estas columnas tal cual:", faltantes)
    print("   Columnas reales en tu archivo:", list(df_crudo.columns))

df = df_crudo.rename(columns=MAPA_COLUMNAS)
for col in MAPA_COLUMNAS.values():
    if col not in df.columns:
        df[col] = ""

muestra = df.sample(n=min(1000, len(df)), random_state=42).reset_index(drop=True)

# Anonimizar
muestra["nombre_recurrente"] = [f"Persona {i}" for i in range(len(muestra))]
muestra["telefono_recurrente"] = [f"9{random.randint(10_000_000, 99_999_999)}" for _ in range(len(muestra))]

# Registrar el lote
hash_archivo = hashlib.sha256(pd.util.hash_pandas_object(muestra).values.tobytes()).hexdigest()
with engine.begin() as conn:
    lote_id = conn.execute(text("""
        INSERT INTO staging.carga_lote (archivo_origen, hash_archivo, cargado_por)
        VALUES (:a, :h, :c) ON CONFLICT (hash_archivo) DO NOTHING RETURNING id
    """), dict(a="muestra_prueba.xlsx", h=hash_archivo, c="prueba_local")).scalar()
if lote_id is None:
    raise SystemExit("Esta muestra ya se cargó antes (mismo hash).")

# Poblar catálogos con los valores únicos que aparecen en la muestra
CATALOGOS_SIMPLES = {
    "operador": "operador", "canal_ingreso": "canal_ingreso", "tipo_recurrente": "tipo_recurrente",
    "area_recurrente": "area_recurrente", "categoria": "categoria", "lugar_tipo": "lugar_tipo",
    "radiooperador": "radiooperador", "inspector": "inspector", "estado": "estado_procedimiento",
    "finalizacion": "finalizacion", "comisaria": "comisaria", "seremi": "seremi",
    "derivacion_comuna": "comuna", "connotacion": "connotacion",
}
for col in CATALOGOS_SIMPLES.keys():
    malos = df[col].apply(lambda x: not isinstance(x, str))
    if malos.any():
        print(f"\nColumna: {col} — {malos.sum()} valores no-texto")
        print(df.loc[malos].head(5))
with engine.begin() as conn:
    for col_df, tabla in CATALOGOS_SIMPLES.items():
        for v in set(x.strip() for x in muestra[col_df] if x.strip()):
            conn.execute(text(f"INSERT INTO catalogo.{tabla} (nombre) VALUES (:v) ON CONFLICT (nombre) DO NOTHING"), dict(v=v))
    for v in set(x.strip() for x in muestra["cuadrante"] if x.strip()):
        conn.execute(text("INSERT INTO catalogo.cuadrante (numero) VALUES (:v) ON CONFLICT (numero) DO NOTHING"), dict(v=v))
    for v in set(x.strip() for x in muestra["movil"] if x.strip()):
        conn.execute(text("INSERT INTO catalogo.movil (codigo) VALUES (:v) ON CONFLICT (codigo) DO NOTHING"), dict(v=v))

    for _, fila in muestra[["categoria", "tipo_procedimiento"]].drop_duplicates().iterrows():
        cat, tipo = fila["categoria"].strip(), fila["tipo_procedimiento"].strip()
        if cat and tipo:
            conn.execute(text("""
                INSERT INTO catalogo.tipo_procedimiento (categoria_id, nombre)
                SELECT id, :t FROM catalogo.categoria WHERE nombre = :c
                ON CONFLICT (categoria_id, nombre) DO NOTHING
            """), dict(c=cat, t=tipo))

def combinar(fecha_base, hora_texto, referencia):
    """Extrae HH:MM de lo que venga (Excel a veces entrega formatos raros al forzar texto)."""
    if not hora_texto:
        return None
    m = re.search(r"(\d{1,2}):(\d{2})", hora_texto)
    if not m:
        return None
    h = dtime(int(m.group(1)) % 24, int(m.group(2)))
    combinado = datetime.combine(fecha_base.date(), h)
    if referencia and combinado < referencia:
        combinado += timedelta(days=1)
    return combinado

def parsear_coordenadas(texto):
    try:
        lat, lon = re.split(r"[,;]\s*", texto.strip())
        return float(lat), float(lon)
    except Exception:
        return None, None

# Insertar reportes, fila por fila y en transacciones separadas
# (así una fila con datos inconsistentes no bota las demás — solo queda como rechazo)
rechazos = []
insertados = 0
with engine.connect() as conn:
    for _, fila in muestra.iterrows():
        fecha_hora = pd.to_datetime(fila["fecha_hora"], dayfirst=True, errors="coerce")
        if pd.isna(fecha_hora):
            rechazos.append((fila["id_legado"], "fecha_hora inválida"))
            continue

        asignacion = combinar(fecha_hora, fila["hora_asignacion_raw"], fecha_hora)
        arribo     = combinar(fecha_hora, fila["hora_arribo_raw"], asignacion or fecha_hora)
        termino    = combinar(fecha_hora, fila["hora_termino_raw"], arribo or asignacion or fecha_hora)
        lat, lon   = parsear_coordenadas(fila["coordenadas"])

        try:
            with conn.begin():
                conn.execute(text("""
                    INSERT INTO core.reporte (
                        id_legado, nro_legado, lote_id, fecha_hora,
                        operador_id, canal_ingreso_id, tipo_recurrente_id, area_recurrente_id,
                        nombre_recurrente, telefono_recurrente, descripcion,
                        categoria_id, tipo_procedimiento_id,
                        calle, numeracion, calle_interseccion, lugar_tipo_id, aclaratoria_ubicacion,
                        cuadrante_id, latitud, longitud,
                        radiooperador_id, movil_id, inspector_id, estado_id,
                        hora_asignacion, hora_arribo, hora_termino,
                        informe, finalizacion_id, apoyo_asistencia,
                        comisaria_id, seremi_id, derivacion_comuna_id, observaciones, connotacion_id,
                        creado_por
                    ) VALUES (
                        :id_legado, :nro_legado, :lote_id, :fecha_hora,
                        (SELECT id FROM catalogo.operador WHERE nombre = :operador),
                        (SELECT id FROM catalogo.canal_ingreso WHERE nombre = :canal_ingreso),
                        (SELECT id FROM catalogo.tipo_recurrente WHERE nombre = :tipo_recurrente),
                        (SELECT id FROM catalogo.area_recurrente WHERE nombre = :area_recurrente),
                        :nombre_recurrente, :telefono_recurrente, :descripcion,
                        (SELECT id FROM catalogo.categoria WHERE nombre = :categoria),
                        (SELECT tp.id FROM catalogo.tipo_procedimiento tp JOIN catalogo.categoria c ON c.id = tp.categoria_id
                            WHERE tp.nombre = :tipo_procedimiento AND c.nombre = :categoria),
                        :calle, :numeracion, :calle_interseccion,
                        (SELECT id FROM catalogo.lugar_tipo WHERE nombre = :lugar_tipo),
                        :aclaratoria_ubicacion,
                        (SELECT id FROM catalogo.cuadrante WHERE numero = :cuadrante),
                        :lat, :lon,
                        (SELECT id FROM catalogo.radiooperador WHERE nombre = :radiooperador),
                        (SELECT id FROM catalogo.movil WHERE codigo = :movil),
                        (SELECT id FROM catalogo.inspector WHERE nombre = :inspector),
                        (SELECT id FROM catalogo.estado_procedimiento WHERE nombre = :estado),
                        :asignacion, :arribo, :termino,
                        :informe,
                        (SELECT id FROM catalogo.finalizacion WHERE nombre = :finalizacion),
                        :apoyo_asistencia,
                        (SELECT id FROM catalogo.comisaria WHERE nombre = :comisaria),
                        (SELECT id FROM catalogo.seremi WHERE nombre = :seremi),
                        (SELECT id FROM catalogo.comuna WHERE nombre = :derivacion_comuna),
                        :observaciones,
                        (SELECT id FROM catalogo.connotacion WHERE nombre = :connotacion),
                        'migracion_prueba'
                    )
                """), dict(
                    id_legado=fila["id_legado"], nro_legado=fila["nro_legado"], lote_id=lote_id,
                    fecha_hora=fecha_hora, operador=fila["operador"].strip(), canal_ingreso=fila["canal_ingreso"].strip(),
                    tipo_recurrente=fila["tipo_recurrente"].strip(), area_recurrente=fila["area_recurrente"].strip(),
                    nombre_recurrente=fila["nombre_recurrente"], telefono_recurrente=fila["telefono_recurrente"],
                    descripcion=fila["descripcion"], categoria=fila["categoria"].strip(),
                    tipo_procedimiento=fila["tipo_procedimiento"].strip(), calle=fila["calle"], numeracion=fila["numeracion"],
                    calle_interseccion=fila["calle_interseccion"], lugar_tipo=fila["lugar_tipo"].strip(),
                    aclaratoria_ubicacion=fila["aclaratoria_ubicacion"], cuadrante=fila["cuadrante"].strip(),
                    lat=lat, lon=lon, radiooperador=fila["radiooperador"].strip(), movil=fila["movil"].strip(),
                    inspector=fila["inspector"].strip(), estado=fila["estado"].strip(),
                    asignacion=asignacion, arribo=arribo, termino=termino,
                    informe=fila["informe"], finalizacion=fila["finalizacion"].strip(),
                    apoyo_asistencia=fila["apoyo_asistencia"], comisaria=fila["comisaria"].strip(),
                    seremi=fila["seremi"].strip(), derivacion_comuna=fila["derivacion_comuna"].strip(),
                    observaciones=fila["observaciones"], connotacion=fila["connotacion"].strip(),
                ))
            insertados += 1
        except Exception as e:
            rechazos.append({
                "id_legado": fila["id_legado"],
                "fecha_hora": fecha_hora,
                "hora_asignacion_raw": fila["hora_asignacion_raw"],
                "hora_arribo_raw": fila["hora_arribo_raw"],
                "hora_termino_raw": fila["hora_termino_raw"],
                "asignacion": asignacion, "arribo": arribo, "termino": termino,
                "error": str(e).replace("\n", " ")[:300],
            })

# print(f"Cargados {insertados} de {len(muestra)} reportes en el lote {lote_id}")
# if rechazos:
#     print(f"{len(rechazos)} rechazados, ejemplos:")
#     for id_, motivo in rechazos[:5]:
#         print(f"  - ID {id_}: {motivo}")

print(f"Cargados {insertados} de {len(muestra)} reportes en el lote {lote_id}")
if rechazos:
    print(f"\n{len(rechazos)} rechazados:")
    for r in rechazos:
        print(r)
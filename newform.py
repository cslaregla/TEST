import streamlit as st
import pandas as pd
from sqlalchemy import text
import time
from geopy.geocoders import ArcGIS
import re

conn = st.connection("db_prueba", type="sql")

def query_segura(sql, ttl=30, params=None, reintentos=2, espera=2):
    for intento in range(reintentos + 1):
        try:
            return conn.query(sql, ttl=ttl, params=params)
        except Exception:
            if intento < reintentos:
                time.sleep(espera); continue
            st.warning("La base de datos está despertando. Recarga la página en unos segundos.")
            st.stop()
#######################################################################################
def geocodificar(calle, numeracion, comuna):
    direccion = f"{calle} {numeracion}, {comuna}, Chile".strip(", ")
    try:
        return tu_funcion_existente(direccion)   # <- tu script de geocodificación real
    except Exception:
        return None, None
def extraer_numero(texto):
    """Extrae el primer número de un string"""
    if pd.isna(texto) or texto == '':
        return ''
    
    texto = str(texto).strip()
    match = re.search(r'\d+', texto)
    
    return match.group() if match else ''
geolocator = ArcGIS(user_agent="geocoder_app")
def construir_direccion(calle, numeracion, interseccion):
    """
    Construye la dirección según los casos:
    - Si hay intersección: CALLE & CALLE QUE INTERSECTA
    - Si hay numeración con número: CALLE NÚMERO
    - Si solo calle: CALLE
    """
    calle = str(calle).strip() if pd.notna(calle) else ''
    numeracion = str(numeracion).strip() if pd.notna(numeracion) else ''
    interseccion = str(interseccion).strip() if pd.notna(interseccion) else ''
    
    # Caso 1: Hay intersección
    if calle and interseccion:
        return f"{calle} & {interseccion}"
    
    # Caso 2: Hay numeración
    if calle and numeracion:
        # Extraer solo el número
        numero = extraer_numero(numeracion)
        if numero:
            return f"{calle} {numero}"
        else:
            return calle
    
    # Caso 3: Solo calle
    if calle:
        return calle
    
    return ''
def obtener_coordenadas(direccion, ciudad='Ñuñoa, Chile'):
    """Obtiene coordenadas de una dirección"""
    try:
        if not direccion or direccion.strip() == '':
            return None
        
        ubicacion = geolocator.geocode(f"{direccion}, {ciudad}", timeout=10)
        
        if ubicacion:
            # Retornar como tupla o string
            return f"{ubicacion.latitude},{ubicacion.longitude}"
        else:
            return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None
#######################################################################################
st.title("Nuevo reporte")

# --- Catálogos: ttl alto porque casi no cambian en una sesión ---
operadores       = query_segura("SELECT nombre FROM catalogo.operador ORDER BY nombre", ttl=300)
canales          = query_segura("SELECT nombre FROM catalogo.canal_ingreso ORDER BY nombre", ttl=300)
tipos_recurrente = query_segura("SELECT nombre FROM catalogo.tipo_recurrente ORDER BY nombre", ttl=300)
areas_recurrente = query_segura("SELECT nombre FROM catalogo.area_recurrente ORDER BY nombre", ttl=300)
categorias       = query_segura("SELECT id, nombre FROM catalogo.categoria ORDER BY nombre", ttl=300)
lugares          = query_segura("SELECT nombre FROM catalogo.lugar_tipo ORDER BY nombre", ttl=300)
cuadrantes       = query_segura("SELECT numero FROM catalogo.cuadrante ORDER BY numero", ttl=300)
comunas          = query_segura("SELECT nombre FROM catalogo.comuna ORDER BY nombre", ttl=300)

# Fuera del form: así el tipo se recalcula al cambiar la categoría
cat_nombre = st.selectbox("Categoría", categorias["nombre"])
cat_id = int(categorias.loc[categorias["nombre"] == cat_nombre, "id"].iloc[0])
tipos = query_segura(
    "SELECT nombre FROM catalogo.tipo_procedimiento WHERE categoria_id = :id ORDER BY nombre",
    params={"id": cat_id}, ttl=60,
)

with st.form("form_ingreso"):
    st.subheader("Datos de la llamada")
    c1, c2 = st.columns(2)
    operador = c1.selectbox("Operador", operadores["nombre"])
    canal = c2.selectbox("Canal de ingreso", canales["nombre"])

    st.subheader("Recurrente")
    c1, c2 = st.columns(2)
    tipo_recurrente = c1.selectbox("Tipo de recurrente", tipos_recurrente["nombre"])
    area_recurrente = c2.selectbox("Área del recurrente", areas_recurrente["nombre"])
    nombre_recurrente = st.text_input("Nombre del recurrente")
    telefono_recurrente = st.text_input("Teléfono del recurrente")

    st.subheader("Procedimiento")
    tipo_procedimiento = st.selectbox(
        "Tipo de procedimiento",
        tipos["nombre"] if not tipos.empty else ["(sin tipos para esta categoría)"],
    )
    descripcion = st.text_area("Descripción del procedimiento")

    st.subheader("Ubicación")
    c1, c2 = st.columns([3, 1])
    calle = c1.text_input("Calle")
    numeracion = c2.text_input("Numeración")
    calle_interseccion = st.text_input("Calle que intersecta")
    c1, c2, c3 = st.columns(3)
    comuna = c1.selectbox("Comuna", comunas["nombre"])
    lugar_tipo = c2.selectbox("Lugar público/privado", lugares["nombre"])
    cuadrante = c3.selectbox("Cuadrante", cuadrantes["numero"])
    aclaratoria = st.text_input("Aclaratoria de la ubicación")

    verificar = st.form_submit_button("Verificar dirección")

if verificar:
    lat, lon = geocodificar(calle, numeracion, comuna) if calle.strip() and numeracion.strip() else (None, None)
    st.session_state["pendiente"] = dict(
        operador=operador, canal=canal, tipo_recurrente=tipo_recurrente, area_recurrente=area_recurrente,
        nombre_recurrente=nombre_recurrente, telefono_recurrente=telefono_recurrente,
        categoria=cat_nombre, tipo_procedimiento=tipo_procedimiento, descripcion=descripcion,
        calle=calle, numeracion=numeracion, calle_interseccion=calle_interseccion,
        comuna=comuna, lugar_tipo=lugar_tipo, cuadrante=cuadrante, aclaratoria=aclaratoria,
        lat=lat, lon=lon,
    )

if "pendiente" in st.session_state:
    d = st.session_state["pendiente"]
    st.subheader("Confirma antes de guardar")
    if d["lat"] is not None:
        st.map(pd.DataFrame([{"lat": d["lat"], "lon": d["lon"]}]), zoom=15)
        st.caption(f"Ubicación encontrada: {d['lat']:.5f}, {d['lon']:.5f}. Verifica que sea el lugar correcto.")
    else:
        st.warning("No se pudo ubicar automáticamente. El reporte se guardará sin coordenadas.")

    if st.button("Confirmar y guardar"):
        for intento in range(3):
            try:
                with conn.session as s:
                    s.execute(text("""
                        INSERT INTO core.reporte (
                            fecha_hora, operador_id, canal_ingreso_id, tipo_recurrente_id, area_recurrente_id,
                            nombre_recurrente, telefono_recurrente, descripcion,
                            categoria_id, tipo_procedimiento_id,
                            calle, numeracion, calle_interseccion, derivacion_comuna_id,
                            lugar_tipo_id, cuadrante_id, aclaratoria_ubicacion,
                            latitud, longitud, estado_id, creado_por
                        ) VALUES (
                            now(),
                            (SELECT id FROM catalogo.operador WHERE nombre = :operador),
                            (SELECT id FROM catalogo.canal_ingreso WHERE nombre = :canal),
                            (SELECT id FROM catalogo.tipo_recurrente WHERE nombre = :tipo_recurrente),
                            (SELECT id FROM catalogo.area_recurrente WHERE nombre = :area_recurrente),
                            :nombre_recurrente, :telefono_recurrente, :descripcion,
                            (SELECT id FROM catalogo.categoria WHERE nombre = :categoria),
                            (SELECT tp.id FROM catalogo.tipo_procedimiento tp JOIN catalogo.categoria c ON c.id = tp.categoria_id
                                WHERE tp.nombre = :tipo_procedimiento AND c.nombre = :categoria),
                            :calle, :numeracion, :calle_interseccion,
                            (SELECT id FROM catalogo.comuna WHERE nombre = :comuna),
                            (SELECT id FROM catalogo.lugar_tipo WHERE nombre = :lugar_tipo),
                            (SELECT id FROM catalogo.cuadrante WHERE numero = :cuadrante),
                            :aclaratoria, :lat, :lon,
                            (SELECT id FROM catalogo.estado_procedimiento WHERE nombre = 'Pendiente'),
                            'app_streamlit'
                        )
                    """), d)
                    s.commit()
                st.success("Reporte guardado correctamente.")
                del st.session_state["pendiente"]
                st.cache_data.clear()
                break
            except Exception:
                if intento < 2:
                    time.sleep(2); continue
                st.error("No se pudo guardar. La base podría estar despertando — intenta de nuevo en unos segundos.")
from sqlalchemy import text
import pandas as pd
import streamlit as st
import time
from geopy.geocoders import ArcGIS
import re

conn = st.connection("db_prueba", type="sql")

st.set_page_config(
    page_title="Planilla de Ingreso",
    page_icon="./logo.png",
    initial_sidebar_state="collapsed",
    layout="wide"
)
st.logo("./logo.png",size='large',icon_image="./logo.png")
st.header("📋 Prueba Planilla de Ingreso")

## Título y botones en una fila ##
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Nuevo Reporte", key="nav_new", width='stretch'):
        st.switch_page("app.py")

with col2:
    if st.button("Actualizar Reporte", key="nav_updt", width='stretch'):
        st.switch_page("pages/1_Actualizar_reporte.py")

with col3:
    if st.button("Visualización", key="nav_view", width='stretch'):
        st.switch_page("pages/2_Vista.py")

def query_segura(conn,sql,ttl=30,params=None,reintentos=2,espera=2):
    for intento in range(reintentos + 1):
        try:
            return conn.query(sql, ttl=ttl, params=params)
        except Exception:
            if intento < reintentos:
                time.sleep(espera)
                continue
        st.warning("La base de datos está despertando. Recarga la página en unos segundos")
        st.stop()
#######################################################################################
geolocator = ArcGIS(user_agent="geocoder_app")
def geocodificar(calle, numeracion, interseccion):

    calle = str(calle).strip() if pd.notna(calle) else ''
    numeracion = str(numeracion).strip() if pd.notna(numeracion) else ''
    interseccion = str(interseccion).strip() if pd.notna(interseccion) else ''
    
    # Caso 1: Hay intersección
    if calle and interseccion:
        direccion = f"{calle} & {interseccion}"
    
    # Caso 2: Hay numeración
    elif calle and numeracion:
        direccion = f"{calle} {numeracion}"
    
    # Caso 3: Solo calle
    elif calle and not numeracion and not interseccion:
        direccion = f"{calle}"
    comuna = 'Ñuñoa, Chile'
    try:
        if not direccion or direccion.strip() == '':
            return None,None
        
        ubicacion = geolocator.geocode(f"{direccion}, {comuna}", timeout=10)
        
        if ubicacion:
            # Retornar como tupla o string
            return ubicacion.latitude,ubicacion.longitude
        else:
            return None,None
    
    except Exception as e:
        print(f"Error: {e}")
        return None,None
#######################################################################################
#categorias = conn.query("SELECT id, nombre FROM catalogo.categoria ORDER BY nombre", ttl=300)
categorias = query_segura(conn,"SELECT id, nombre FROM catalogo.categoria ORDER BY nombre", ttl=300)
cat_nombre = st.selectbox("Categoría", categorias["nombre"])   # fuera del form: se actualiza al instante
cat_id = int(categorias.loc[categorias["nombre"] == cat_nombre, "id"].iloc[0])

# tipos = conn.query(
#     "SELECT nombre FROM catalogo.tipo_procedimiento WHERE categoria_id = :id ORDER BY nombre",
#     params={"id": cat_id}, ttl=60
# )
# estados = conn.query("SELECT nombre FROM catalogo.estado_procedimiento ORDER BY nombre", ttl=300)
tipos = query_segura(conn,
    "SELECT nombre FROM catalogo.tipo_procedimiento WHERE categoria_id = :id ORDER BY nombre",
    params={"id": cat_id}, ttl=60
)

calles = query_segura(conn, "SELECT nombre FROM catalogo.calle ORDER BY nombre", ttl=300 )
canales = query_segura(conn, "SELECT nombre FROM catalogo.canal_ingreso ORDER BY nombre", ttl=300 )
operadores = query_segura(conn, "SELECT nombre FROM catalogo.operador ORDER BY nombre", ttl=300 )
tipos_recurrentes = query_segura(conn, "SELECT nombre FROM catalogo.tipo_recurrente ORDER BY nombre", ttl=300 )
areas_recurrentes = query_segura(conn, "SELECT nombre FROM catalogo.area_recurrente ORDER BY nombre", ttl=300 )
lugares_tipos = query_segura(conn, "SELECT nombre FROM catalogo.lugar_tipo ORDER BY nombre", ttl=300 )
cuadrantes = query_segura(conn, "SELECT numero FROM catalogo.cuadrante ORDER BY numero", ttl=300 )
radiooperadores = query_segura(conn, "SELECT nombre FROM catalogo.radiooperador ORDER BY nombre", ttl=300 )
moviles = query_segura(conn, "SELECT codigo FROM catalogo.movil ORDER BY codigo", ttl=300 )
inspectores = query_segura(conn, "SELECT nombre FROM catalogo.inspector ORDER BY nombre", ttl=300 )
estados = query_segura(conn,"SELECT nombre FROM catalogo.estado_procedimiento ORDER BY nombre",ttl=300)
finalizaciones = query_segura(conn,"SELECT nombre FROM catalogo.finalizacion ORDER BY nombre",ttl=300)
apoyos = query_segura(conn,"SELECT nombre FROM catalogo.apoyo_asistencia ORDER BY nombre",ttl=300)
comisarias = query_segura(conn,"SELECT nombre FROM catalogo.comisaria ORDER BY nombre",ttl=300)
seremis = query_segura(conn,"SELECT nombre FROM catalogo.seremi ORDER BY nombre",ttl=300)

with st.form("form_prueba", clear_on_submit=True):
    operador = st.selectbox("Operador", operadores["nombre"], index=None)
    canal_ing = st.selectbox("Vía/Canal de Ingreso", canales["nombre"], index=None)
    f1, f2 = st.columns(2)
    with f1:
        tipo_recurrente = st.selectbox("Tipo de Recurrente", tipos_recurrentes["nombre"], index=None)
    with f2:
        area_recurrente = st.selectbox("Area o Sección del Recurrente", areas_recurrentes["nombre"], index=None)
    f3,f4 = st.columns(2)
    with f3:
        nombre_recurrente = st.text_input("Nombre del Recurrente")
    with f4:
        telefono_recurrente = st.text_input("Teléfono del Recurrente")
    tipo = st.selectbox("Tipo de procedimiento", tipos["nombre"] if not tipos.empty else ["(sin tipos aún)"])
    descripcion = st.text_area("Descripción del Procedimiento")
    f5,f6,f7 = st.columns(3)
    with f5:
        calle = st.selectbox("Calle", calles["nombre"], index=None,placeholder='Ingrese una calle')
    with f6:
        numeracion = st.number_input("Numeración", min_value=1,step=1,value=None, help="Dejar en blanco si es una intersección")
    with f7:
        calle_esq = st.selectbox("Calle que Intersecta", calles["nombre"], index=None,placeholder='De ser intersección, ingrese una calle')
    lugar_tipo = st.selectbox("Lugar Público/Privado", lugares_tipos["nombre"], index=None, placeholder='Tipo de Lugar')
    aclaratoria_ubicacion = st.text_input("Aclaratoria de la ubicación")
    cuadrante = st.selectbox("Cuadrante", cuadrantes["numero"], index=None)
    f8, f9 = st.columns(2)
    with f8:
        radiooperador = st.selectbox("Radioperador de Turno", radiooperadores["nombre"], index=None)
    with f9:
        movil = st.selectbox("Número de Móvil", moviles["codigo"], index=None)
    inspector = st.selectbox("Inspector Asignado", inspectores["nombre"], index=None)
    estado = st.selectbox("Estado", estados["nombre"],index=None, placeholder='¿Cuál es el estado del procedimiento?')
    #informe = st.text_input("INFORME")
    #finalizacion = st.selectbox("Finalización", finalizaciones["nombre"],index=None, placeholder='Finalización')
    #apoyo_asistencia = st.selectbox("Apoyo o Asistencia", apoyos["nombre"],index=None, placeholder='Apoyo o asistencia')
    f10, f11 = st.columns(2)
    with f10:
        comisaria = st.selectbox("Comisaría", comisarias["nombre"],index=None)
    with f11:
        seremi = st.selectbox("Seremi", seremis["nombre"],index=None)
    #observaciones = st.text_input("OBSERVACIONES")
    #connotacion = st.text_input("Connotación")
    enviado = st.form_submit_button("GUARDAR REPORTE")

if enviado:
    lat,lon = geocodificar(calle,numeracion,calle_esq)
    with conn.session as s:
        nuevo_id = s.execute(text("""
            INSERT INTO core.reporte
                (fecha_hora,
                operador_id,
                canal_ingreso_id,
                tipo_recurrente_id,
                area_recurrente_id,
                nombre_recurrente,
                telefono_recurrente,
                categoria_id, 
                tipo_procedimiento_id,
                descripcion,
                calle_id,
                numeracion,
                calle_interseccion_id,
                lugar_tipo_id,
                aclaratoria_ubicacion,
                cuadrante_id,
                radiooperador_id,
                movil_id,
                inspector_id,
                estado_id,
                comisaria_id,
                seremi_id,
                latitud,
                longitud,
                creado_por)
            VALUES 
                (now(),
                (SELECT id FROM catalogo.operador WHERE nombre = :operador),
                (SELECT id FROM catalogo.canal_ingreso WHERE nombre = :canal_ing),
                (SELECT id FROM catalogo.tipo_recurrente WHERE nombre = :tipo_recurrente),
                (SELECT id FROM catalogo.area_recurrente WHERE nombre = :area_recurrente),
                :nombre_recurrente,
                :telefono_recurrente,
                :cat_id,
                (SELECT id FROM catalogo.tipo_procedimiento WHERE nombre = :tipo AND categoria_id = :cat_id),
                :desc,
                (SELECT id FROM catalogo.calle WHERE nombre = :calle),
                :numeracion,
                (SELECT id FROM catalogo.calle WHERE nombre = :calle_esq),
                (SELECT id FROM catalogo.lugar_tipo WHERE nombre = :lugar_tipo),
                :aclaratoria_ubicacion,
                (SELECT id FROM catalogo.cuadrante WHERE numero = :cuadrante),
                (SELECT id FROM catalogo.radiooperador WHERE nombre = :radiooperador),
                (SELECT id FROM catalogo.movil WHERE codigo = :movil),
                (SELECT id FROM catalogo.inspector WHERE nombre = :inspector),
                (SELECT id FROM catalogo.estado_procedimiento WHERE nombre = :estado),
                (SELECT id FROM catalogo.comisaria WHERE nombre = :comisaria),
                (SELECT id FROM catalogo.seremi WHERE nombre = :seremi),
                :lat, 
                :lon,
                'prueba_streamlit')
            RETURNING id
        """), dict(cat_id=cat_id, operador=operador, canal_ing=canal_ing, tipo_recurrente=tipo_recurrente, area_recurrente=area_recurrente, nombre_recurrente=nombre_recurrente, 
                   telefono_recurrente=telefono_recurrente, tipo=tipo, desc=descripcion, calle=calle, numeracion=numeracion, calle_esq=calle_esq, lugar_tipo=lugar_tipo,
                   aclaratoria_ubicacion=aclaratoria_ubicacion, cuadrante=cuadrante, radiooperador=radiooperador, movil=movil, inspector=inspector, estado=estado,
                   comisaria=comisaria, seremi=seremi, lat=lat, lon=lon)).scalar()
        s.commit()
    st.cache_data.clear()
    st.success(f"Guardado. FOLIO: {nuevo_id} — revisa la página de visualización.")
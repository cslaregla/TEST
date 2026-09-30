from sqlalchemy import text
import pandas as pd
import streamlit as st
import time

conn = st.connection("db_prueba", type="sql")

st.set_page_config(
    page_title="Planilla de Ingreso",
    page_icon="./logo.png",
    initial_sidebar_state="collapsed",
    layout="wide"
)
st.logo("./logo.png",size='large',icon_image="./logo.png")
st.header("📋 Prueba Planilla de Ingreso")

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
estados = query_segura(conn,"SELECT nombre FROM catalogo.estado_procedimiento ORDER BY nombre",ttl=300)

with st.form("form_prueba", clear_on_submit=True):
    tipo = st.selectbox("Tipo de procedimiento", tipos["nombre"] if not tipos.empty else ["(sin tipos aún)"])
    estado = st.selectbox("Estado", estados["nombre"])
    descripcion = st.text_area("Descripción")
    calle = st.text_input("Calle")
    numeracion = st.text_input("Numeración")
    col1, col2 = st.columns(2)
    lat = col1.number_input("Latitud", value=-33.45, format="%.6f")
    lon = col2.number_input("Longitud", value=-70.65, format="%.6f")
    enviado = st.form_submit_button("Guardar")

if enviado:
    with conn.session as s:
        s.execute(text("""
            INSERT INTO core.reporte
                (fecha_hora, categoria_id, tipo_procedimiento_id, estado_id, descripcion, latitud, longitud, creado_por)
            VALUES (now(), :cat_id,
                (SELECT id FROM catalogo.tipo_procedimiento WHERE nombre = :tipo AND categoria_id = :cat_id),
                (SELECT id FROM catalogo.estado_procedimiento WHERE nombre = :estado),
                :desc, :lat, :lon, 'prueba_streamlit')
        """), dict(cat_id=cat_id, tipo=tipo, estado=estado, desc=descripcion, lat=lat, lon=lon))
        s.commit()
    st.cache_data.clear()
    st.success("Guardado — revisa la tabla, el gráfico y el mapa de abajo")

st.divider()
st.header("Lo que ve el análisis, justo después")

# datos = conn.query("""
#     SELECT r.fecha_hora, c.nombre AS categoria, r.latitud, r.longitud
#     FROM core.reporte r JOIN catalogo.categoria c ON c.id = r.categoria_id
#     ORDER BY r.fecha_hora DESC
# """, ttl=30)
datos = query_segura(conn,"""
    SELECT r.fecha_hora, c.nombre AS categoria, r.latitud, r.longitud
    FROM core.reporte r JOIN catalogo.categoria c ON c.id = r.categoria_id
    ORDER BY r.fecha_hora DESC
""",ttl=30)
# datos_tabla = conn.query("""
#     SELECT r.creado_en, r.fecha_hora, c.nombre AS categoria, r.descripcion
#     FROM core.reporte r JOIN catalogo.categoria c ON c.id = r.categoria_id
#     ORDER BY r.creado_en DESC
#     LIMIT 20
# """, ttl=10)
datos_tabla = query_segura(conn,"""
    SELECT r.creado_en, r.fecha_hora, c.nombre AS categoria, r.descripcion
    FROM core.reporte r JOIN catalogo.categoria c ON c.id = r.categoria_id
    ORDER BY r.creado_en DESC
    LIMIT 20
""",ttl=10)
datos_tabla["fecha_hora"] = (
    pd.to_datetime(datos_tabla["fecha_hora"], utc=True)
      .dt.tz_convert("America/Santiago")
      .dt.strftime("%d-%m-%Y %H:%M")
)
st.dataframe(datos_tabla, width='stretch', height=400)
st.bar_chart(datos["categoria"].value_counts())

mapa = datos.dropna(subset=["latitud", "longitud"]).rename(columns={"latitud": "lat", "longitud": "lon"})
if not mapa.empty:
    st.map(mapa[["lat", "lon"]],zoom=12, size=30)
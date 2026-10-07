import streamlit as st
import time

st.set_page_config(
    page_title="Visualización de la Información",
    page_icon="./logo.png",
    initial_sidebar_state="collapsed",
    layout="wide"
)

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

conn = st.connection("db_prueba", type="sql")
st.header("💾 Visualización Planilla de Ingreso")

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

datos = query_segura(conn,"""
    SELECT r.fecha_hora, c.nombre AS categoria, r.latitud, r.longitud
    FROM core.reporte r JOIN catalogo.categoria c ON c.id = r.categoria_id
    ORDER BY r.fecha_hora DESC
""",ttl=30)

datos_tabla = query_segura(conn,"""
    SELECT r.creado_en, r.fecha_hora, c.nombre AS categoria, r.descripcion
    FROM core.reporte r JOIN catalogo.categoria c ON c.id = r.categoria_id
    ORDER BY r.creado_en DESC
    LIMIT 50
""",ttl=10)

st.dataframe(
    datos_tabla,
    column_config={
        "fecha_hora": st.column_config.DatetimeColumn(
            "Fecha y hora",
            format="DD-MM-YYYY HH:mm",
            timezone="America/Santiago")
    },
    width='stretch', height=400)
st.bar_chart(datos["categoria"].value_counts(),color="#c92305")

mapa = datos.dropna(subset=["latitud", "longitud"]).rename(columns={"latitud": "lat", "longitud": "lon"})
if not mapa.empty:
    st.map(mapa[["lat", "lon"]], zoom=12, size=30)
from sqlalchemy import text
import pandas as pd
import streamlit as st
import time
from geopy.geocoders import ArcGIS
import re

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
######################

conn = st.connection("db_prueba", type="sql")
st.header("💾 Visualización Planilla de Ingreso")

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
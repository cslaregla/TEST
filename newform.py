import streamlit as st
from sqlalchemy import text
conn = st.connection("db_prueba", type="sql")

# Reemplaza el cuerpo de esta función por tu script existente de calle → coordenadas
def geocodificar(calle: str, numeracion: str, comuna: str = "") -> tuple:
    direccion = f"{calle} {numeracion}, {comuna}, Chile".strip(", ")
    try:
        lat, lon = tu_funcion_existente(direccion)   # <- tu lógica real aquí
        return lat, lon
    except Exception:
        return None, None

@st.cache_data(ttl=86400)   # evita volver a geocodificar la misma dirección dentro de un día
def geocodificar_cacheado(calle, numeracion, comuna):
    return geocodificar(calle, numeracion, comuna)

with st.form("form_ingreso", clear_on_submit=True):
    # ... resto de los campos de ingreso ...
    calle = st.text_input("Calle")
    numeracion = st.text_input("Numeración")
    comuna = st.selectbox("Comuna", comunas["nombre"])
    enviado = st.form_submit_button("Guardar")

if enviado:
    lat, lon = (None, None)
    if calle.strip() and numeracion.strip():
        lat, lon = geocodificar_cacheado(calle, numeracion, comuna)

    if lat is None and calle.strip():
        st.warning("No se pudo obtener la ubicación automáticamente. "
                    "El reporte se guardará igual, sin coordenadas — se puede completar después.")

    with conn.session as s:
        s.execute(text("""
            INSERT INTO core.reporte (fecha_hora, calle, numeracion, comuna_id, latitud, longitud, ...)
            VALUES (now(), :calle, :numeracion,
                    (SELECT id FROM catalogo.comuna WHERE nombre = :comuna),
                    :lat, :lon, ...)
        """), dict(calle=calle, numeracion=numeracion, comuna=comuna, lat=lat, lon=lon, ...))
        s.commit()

    st.cache_data.clear()
    st.success("Reporte guardado" + (f" — ubicado en {lat:.5f}, {lon:.5f}" if lat else " (sin coordenadas)"))
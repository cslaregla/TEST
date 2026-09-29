import streamlit as st

conn = st.connection("db_prueba", type="sql")

st.header("Buscar reporte")
criterio = st.text_input("Folio, o parte de la dirección/descripción")

if criterio:
    resultados = conn.query("""
        SELECT id, fecha_hora, descripcion, calle
        FROM core.reporte
        WHERE id::text = :c OR descripcion ILIKE :like OR calle ILIKE :like
        ORDER BY fecha_hora DESC LIMIT 20
    """, params={"c": criterio, "like": f"%{criterio}%"}, ttl=5)

    if resultados.empty:
        st.info("No se encontraron reportes con ese criterio.")
    else:
        fila_id = st.selectbox("Selecciona el reporte", resultados["id"])
        # ... cargar la fila completa y mostrar el formulario pre-llenado con sus valores
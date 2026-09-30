# categorias_tipos.csv → columnas: categoria, tipo
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg://...")
tabla = pd.read_csv("categorias_tipos.csv", dtype=str. sep=';', encoding='utf-8')

with engine.begin() as conn:
    for cat in tabla["categoria"].dropna().unique():
        conn.execute(text("INSERT INTO catalogo.categoria (nombre) VALUES (:c) ON CONFLICT (nombre) DO NOTHING"), dict(c=cat.strip()))
    for _, fila in tabla.dropna(subset=["categoria", "tipo"]).iterrows():
        conn.execute(text("""
            INSERT INTO catalogo.tipo_procedimiento (categoria_id, nombre)
            SELECT id, :t FROM catalogo.categoria WHERE nombre = :c
            ON CONFLICT (categoria_id, nombre) DO NOTHING
        """), dict(c=fila["categoria"].strip(), t=fila["tipo"].strip()))
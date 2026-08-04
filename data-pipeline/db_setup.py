"""
Crea la tabla 'clima' en PostgreSQL si no existe.
Ejecutar una sola vez antes de correr fetch_weather.py:

    python db_setup.py
"""

import psycopg2
from config import DB_DSN

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS clima (
    fecha            DATE PRIMARY KEY,
    temp_max         REAL,
    temp_min         REAL,
    temp_media       REAL,
    humedad          REAL,
    viento_max       REAL,
    nubosidad        REAL,
    precipitacion    REAL,
    creado_en        TIMESTAMP DEFAULT NOW()
);
"""


def main():
    print(f"Conectando a la base de datos...")
    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()
        print("Tabla 'clima' lista.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
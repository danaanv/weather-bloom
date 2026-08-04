"""
Trae datos de clima de Lima desde Open-Meteo y los guarda en PostgreSQL.

Uso:
    # Traer histórico (una sola vez, para poblar el jardín con meses/años pasados)
    python fetch_weather.py --start 2024-01-01 --end 2026-07-31

    # Traer solo el día de ayer (uso diario, ideal para correr en un cron/GitHub Action)
    python fetch_weather.py --daily
"""

import argparse
import sys
from datetime import date, timedelta

import psycopg2
import requests

from config import (
    ARCHIVE_URL,
    FORECAST_URL,
    LIMA_LATITUDE,
    LIMA_LONGITUDE,
    TIMEZONE,
    DAILY_VARIABLES,
    DB_DSN,
)

UPSERT_SQL = """
INSERT INTO clima (fecha, temp_max, temp_min, temp_media, humedad, viento_max, nubosidad, precipitacion)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (fecha) DO UPDATE SET
    temp_max = EXCLUDED.temp_max,
    temp_min = EXCLUDED.temp_min,
    temp_media = EXCLUDED.temp_media,
    humedad = EXCLUDED.humedad,
    viento_max = EXCLUDED.viento_max,
    nubosidad = EXCLUDED.nubosidad,
    precipitacion = EXCLUDED.precipitacion;
"""


def fetch_range(start_date: str, end_date: str) -> dict:
    """Trae datos históricos de un rango de fechas usando el endpoint archive."""
    params = {
        "latitude": LIMA_LATITUDE,
        "longitude": LIMA_LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": TIMEZONE,
    }
    resp = requests.get(ARCHIVE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_recent(days_back: int = 1) -> dict:
    """Trae datos recientes (ej. ayer) usando el endpoint forecast con past_days."""
    params = {
        "latitude": LIMA_LATITUDE,
        "longitude": LIMA_LONGITUDE,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": TIMEZONE,
        "past_days": days_back,
        "forecast_days": 1,
    }
    resp = requests.get(FORECAST_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def rows_from_payload(payload: dict):
    """Convierte la respuesta JSON de Open-Meteo en filas listas para insertar."""
    daily = payload.get("daily", {})
    fechas = daily.get("time", [])

    for i, fecha in enumerate(fechas):
        yield (
            fecha,
            daily.get("temperature_2m_max", [None] * len(fechas))[i],
            daily.get("temperature_2m_min", [None] * len(fechas))[i],
            daily.get("temperature_2m_mean", [None] * len(fechas))[i],
            daily.get("relative_humidity_2m_mean", [None] * len(fechas))[i],
            daily.get("windspeed_10m_max", [None] * len(fechas))[i],
            daily.get("cloudcover_mean", [None] * len(fechas))[i],
            daily.get("precipitation_sum", [None] * len(fechas))[i],
        )


def save_rows(rows) -> int:
    """Guarda las filas en PostgreSQL (upsert por fecha). Retorna cuántas se guardaron."""
    rows = list(rows)
    if not rows:
        return 0

    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, rows)
        conn.commit()
    finally:
        conn.close()

    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Fetch de clima de Lima (Open-Meteo -> PostgreSQL)")
    parser.add_argument("--start", help="Fecha inicio para carga histórica (YYYY-MM-DD)")
    parser.add_argument("--end", help="Fecha fin para carga histórica (YYYY-MM-DD)")
    parser.add_argument("--daily", action="store_true", help="Traer solo el día de ayer (uso en cron diario)")
    args = parser.parse_args()

    if args.daily:
        print("Trayendo clima del día de ayer...")
        payload = fetch_recent(days_back=1)
    elif args.start and args.end:
        print(f"Trayendo histórico de {args.start} a {args.end}...")
        payload = fetch_range(args.start, args.end)
    else:
        # Default: si no se especifica nada, trae el último año
        end = date.today() - timedelta(days=1)
        start = end - timedelta(days=365)
        print(f"Sin fechas especificadas. Trayendo último año: {start} a {end}...")
        payload = fetch_range(start.isoformat(), end.isoformat())

    rows = rows_from_payload(payload)
    total = save_rows(rows)
    print(f"Listo. {total} días guardados/actualizados en la base de datos.")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as e:
        print(f"Error llamando a la API de Open-Meteo: {e}", file=sys.stderr)
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"Error de base de datos: {e}", file=sys.stderr)
        sys.exit(1)
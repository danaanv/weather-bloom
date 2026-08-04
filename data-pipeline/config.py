"""
Configuración central del pipeline de datos.
Lee variables de entorno (ver .env.example) para no hardcodear credenciales.
"""

import os
from dotenv import load_dotenv

# Carga variables desde el archivo .env (ubicado en la raíz del repo)
load_dotenv()

# --- Base de datos ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "lima_weather")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DB_DSN = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"

# --- Ubicación: Lima, Perú ---
LIMA_LATITUDE = -12.0464
LIMA_LONGITUDE = -77.0428
TIMEZONE = "America/Lima"

# --- Open-Meteo API (no requiere API key) ---
# Endpoint histórico (archive) - para traer meses/años pasados de una vez
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
# Endpoint forecast - también sirve para traer el día actual/reciente
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Variables diarias que pedimos a la API
DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "windspeed_10m_max",
    "cloudcover_mean",
    "precipitation_sum",
]
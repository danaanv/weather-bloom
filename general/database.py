"""Acceso a datos climáticos desde PostgreSQL con fallback seguro."""

import math
import os
from datetime import date, timedelta

import psycopg2


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "lima_weather")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", os.getenv("DB_PASSWORD", "postgres"))

DEFAULT_WEATHER = {
	"fecha": None,
	"temp_max": 21.0,
	"temp_min": 14.0,
	"temp_media": 17.5,
	"humedad": 58.0,
	"viento_max": 11.0,
	"nubosidad": 32.0,
	"precipitacion": 0.0,
}


def _conectar_postgresql():
	"""Crea una conexión a PostgreSQL usando la configuración global."""

	return psycopg2.connect(
		host=DB_HOST,
		port=DB_PORT,
		dbname=DB_NAME,
		user=DB_USER,
		password=DB_PASS,
	)


def limitar_valor(valor, minimo, maximo):
	"""Recorta un valor numérico para mantenerlo dentro de un rango seguro."""

	return max(minimo, min(maximo, valor))


def normalizar_registro_clima(fila):
	"""Convierte una fila de PostgreSQL en un diccionario homogéneo para la escena."""

	if not fila:
		return DEFAULT_WEATHER.copy()

	def _como_float(valor, predeterminado):
		return float(valor) if valor is not None else float(predeterminado)

	return {
		"fecha": fila.get("fecha"),
		"temp_max": _como_float(fila.get("temp_max"), DEFAULT_WEATHER["temp_max"]),
		"temp_min": _como_float(fila.get("temp_min"), DEFAULT_WEATHER["temp_min"]),
		"temp_media": _como_float(fila.get("temp_media"), DEFAULT_WEATHER["temp_media"]),
		"humedad": _como_float(fila.get("humedad"), DEFAULT_WEATHER["humedad"]),
		"viento_max": _como_float(fila.get("viento_max"), DEFAULT_WEATHER["viento_max"]),
		"nubosidad": _como_float(fila.get("nubosidad"), DEFAULT_WEATHER["nubosidad"]),
		"precipitacion": _como_float(fila.get("precipitacion"), DEFAULT_WEATHER["precipitacion"]),
	}


def get_mock_month_data():
	"""Genera un mes de prueba con 31 registros climáticos simulados."""

	registros = []
	fecha_inicial = date(2026, 5, 1)

	for indice in range(31):
		progreso = indice / 30.0
		angulo = progreso * math.tau
		temp_media = 15.5 + math.sin(angulo - 0.55) * 8.3 + math.sin(angulo * 2.2) * 1.1
		humedad = 56.0 + math.cos(angulo + 0.8) * 16.5 + math.sin(angulo * 1.6) * 3.0
		precipitacion = max(0.0, 2.2 + math.sin(angulo + 1.45) * 2.6 + math.cos(angulo * 1.9) * 0.7)

		registros.append(
			{
				"fecha": (fecha_inicial + timedelta(days=indice)).isoformat(),
				"temp_media": round(temp_media, 1),
				"precipitacion": round(precipitacion, 1),
				"humedad": round(limitar_valor(humedad, 20.0, 98.0), 1),
			}
		)

	return registros


def load_monthly_weather_data():
	"""Carga los últimos 31 registros de clima en orden ascendente."""

	consulta = (
		"SELECT * FROM ("
		"SELECT fecha, temp_max, temp_min, temp_media, humedad, viento_max, nubosidad, precipitacion "
		"FROM clima ORDER BY fecha DESC LIMIT 31"
		") AS ultimos_registros ORDER BY fecha ASC;"
	)
	conexion = None

	try:
		conexion = _conectar_postgresql()
		with conexion.cursor() as cursor:
			cursor.execute(consulta)
			filas = cursor.fetchall()
			if not filas:
				print("PostgreSQL no devolvió filas mensuales. Se usará mock mensual.")
				return get_mock_month_data()

			columnas = [columna[0] for columna in cursor.description]
			registros = [normalizar_registro_clima(dict(zip(columnas, fila))) for fila in filas]
			if len(registros) < 31:
				print("PostgreSQL devolvió menos de 31 días. Se completará con mock mensual.")
				mock = get_mock_month_data()
				return mock[: 31 - len(registros)] + registros
			return registros
	except psycopg2.Error as error:
		print(f"No se pudo cargar el mes desde PostgreSQL ({error}). Se usará mock mensual.")
		return get_mock_month_data()
	finally:
		if conexion is not None:
			conexion.close()


def load_latest_day_data():
	"""Carga el registro más reciente de la tabla clima."""

	consulta = "SELECT * FROM clima ORDER BY fecha DESC LIMIT 1;"
	conexion = None

	try:
		conexion = _conectar_postgresql()
		with conexion.cursor() as cursor:
			cursor.execute(consulta)
			fila = cursor.fetchone()
			if not fila:
				print("PostgreSQL respondió vacío. Se usará el último dato mock.")
				return normalizar_registro_clima(get_mock_month_data()[-1])

			columnas = [columna[0] for columna in cursor.description]
			registro = dict(zip(columnas, fila))
			return normalizar_registro_clima(registro)
	except psycopg2.Error as error:
		print(f"No se pudo cargar el último día desde PostgreSQL ({error}). Se usará mock reciente.")
		return normalizar_registro_clima(get_mock_month_data()[-1])
	finally:
		if conexion is not None:
			conexion.close()

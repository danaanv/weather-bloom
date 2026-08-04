"""Entorno base del jardín interactivo en Pygame.

Este paso solo construye la base estética: ventana, cielo degradado,
luna con resplandor y partículas tipo luciérnaga.
"""

import math
import os
import random
import sys
from datetime import date, timedelta

import pygame
import psycopg2


ANCHO = 1000
ALTO = 650
FPS = 60
NUMERO_PARTICULAS = 70
NUMERO_PARTICULAS_FONDO = 45
NUMERO_PARTICULAS_FRENTE = NUMERO_PARTICULAS - NUMERO_PARTICULAS_FONDO
NUMERO_TULIPANES_FONDO = 10
NUMERO_TULIPANES_MEDIO = 13
NUMERO_TULIPANES_FRENTE = 16

MODO_DIA = "dia"
MODO_NOCHE = "noche"

INDIGO_PROFUNDO = (22, 26, 67)
MELCOCO_TIBIO = (255, 196, 166)
CELESTE_PASTEL = (187, 226, 248)
BLANCO_SUAVE = (248, 250, 255)
AMARILLO_SOL = (255, 236, 182)
ROSA_PETALO = (255, 196, 214)
ROSA_PETALO_CLARO = (255, 226, 235)
LUNA_BASE = (244, 236, 205)
LUNA_BRILLO = (255, 248, 224)
SOL_BASE = (255, 232, 170)
SOL_BRILLO = (255, 246, 214)
LUCIERNAGA_NUCLEO = (255, 245, 160)
LUCIERNAGA_AUREOLA = (255, 214, 95)

COLINA_FONDO = (28, 40, 72)
COLINA_MEDIA = (20, 74, 80)
COLINA_FRENTE = (18, 58, 34)

TULIPAN_FONDO_BASE = (74, 84, 122)
TULIPAN_MEDIO_BASE = (56, 128, 124)
TULIPAN_FRENTE_BASE = (214, 92, 124)

TALLO_FONDO = (45, 72, 54)
TALLO_MEDIO = (34, 92, 64)
TALLO_FRENTE = (24, 112, 58)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "lima_weather")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

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


def limitar_valor(valor, minimo, maximo):
	"""Recorta un valor numérico para mantenerlo dentro de un rango seguro."""

	return max(minimo, min(maximo, valor))


def interpolar_color_base(color_inicial, color_final, factor):
	"""Interpola dos colores RGB para construir atmósferas más suaves."""

	factor = limitar_valor(factor, 0.0, 1.0)
	return tuple(
		int(color_inicial[indice] + (color_final[indice] - color_inicial[indice]) * factor)
		for indice in range(3)
	)


def desaturar_color(color, intensidad):
	"""Reduce saturación empujando el color hacia un gris medio cálido."""

	intensidad = limitar_valor(intensidad, 0.0, 1.0)
	gris = sum(color) / 3.0
	return tuple(int(canal * (1.0 - intensidad) + gris * intensidad) for canal in color)


def normalizar_registro_clima(fila):
	"""Convierte la fila de PostgreSQL en un diccionario listo para la escena."""

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


def load_latest_weather_data():
	"""Carga el registro climático más reciente desde PostgreSQL.

	Si la base de datos no responde, está vacía o el contenedor no está levantado,
	retorna una paleta climática por defecto para que la escena siga funcionando.
	"""

	consulta = "SELECT * FROM clima ORDER BY fecha DESC LIMIT 1;"
	conexion = None

	try:
		conexion = psycopg2.connect(
			host=DB_HOST,
			port=DB_PORT,
			dbname=DB_NAME,
			user=DB_USER,
			password=DB_PASSWORD,
		)
		with conexion.cursor() as cursor:
			cursor.execute(consulta)
			fila = cursor.fetchone()
			if not fila:
				print("PostgreSQL respondió, pero la tabla 'clima' está vacía. Se usará fallback.")
				return DEFAULT_WEATHER.copy()

			columnas = [columna[0] for columna in cursor.description]
			registro = dict(zip(columnas, fila))
			print(f"Clima más reciente cargado desde PostgreSQL: {registro.get('fecha')}")
			return normalizar_registro_clima(registro)
	except psycopg2.Error as error:
		print(f"No se pudo leer PostgreSQL ({error}). Se usará fallback climático.")
		return DEFAULT_WEATHER.copy()
	finally:
		if conexion is not None:
			conexion.close()


def interpolar_color(color_superior, color_inferior, progreso):
	"""Interpola dos colores RGB en función de un progreso entre 0 y 1."""

	return tuple(
		int(color_superior[i] + (color_inferior[i] - color_superior[i]) * progreso)
		for i in range(3)
	)


def ajustar_brillo(color, factor):
	"""Aclara u oscurece un color RGB multiplicando cada canal por un factor."""

	return tuple(max(0, min(255, int(canal * factor))) for canal in color)


def crear_paleta_tulipan(color_base, color_tallo, grosor_tallo):
	"""Construye una paleta coherente para el cuerpo del tulipán y su tallo."""

	return {
		"petalo_izq": ajustar_brillo(color_base, 0.88),
		"petalo_centro": ajustar_brillo(color_base, 1.08),
		"petalo_der": ajustar_brillo(color_base, 0.98),
		"tallo": color_tallo,
		"grosor_tallo": grosor_tallo,
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


def lerp(valor_inicial, valor_final, factor):
	"""Interpola linealmente dos valores numéricos."""

	factor = limitar_valor(factor, 0.0, 1.0)
	return valor_inicial + (valor_final - valor_inicial) * factor


def lerp_color(color_inicial, color_final, factor):
	"""Interpola linealmente dos colores RGB canal por canal."""

	factor = limitar_valor(factor, 0.0, 1.0)
	return tuple(
		int(lerp(color_inicial[indice], color_final[indice], factor))
		for indice in range(3)
	)


def calcular_paleta_por_temperatura(temp_media, temp_min, temp_max):
	"""Convierte la temperatura del día en una paleta fría o cálida para el tulipán."""

	temp_min = float(temp_min)
	temp_max = float(temp_max)
	if temp_max <= temp_min:
		normalizado = 0.5
	else:
		normalizado = (float(temp_media) - temp_min) / (temp_max - temp_min)

	normalizado = limitar_valor(normalizado, 0.0, 1.0)
	color_base = lerp_color((180, 196, 255), (255, 178, 124), normalizado)
	color_borde = lerp_color((162, 176, 248), (242, 132, 102), normalizado)
	color_luz = lerp_color((233, 236, 255), (255, 244, 214), normalizado)
	color_tallo = lerp_color((54, 126, 88), (38, 108, 64), normalizado)

	return {
		"petalo_izq": ajustar_brillo(color_borde, 0.92),
		"petalo_centro": color_luz,
		"petalo_der": ajustar_brillo(color_base, 1.02),
		"tallo": color_tallo,
		"grosor_tallo": 3,
	}


class FondoAesthetic:
	"""Dibuja un degradado vertical suave para simular un cielo crepuscular."""

	def __init__(self, ancho, alto, nubosidad):
		self.ancho = ancho
		self.alto = alto
		self.nubosidad = limitar_valor(float(nubosidad), 0.0, 100.0)
		self._actualizar_paleta()

	def _actualizar_paleta(self):
		"""Atenúa los colores base cuando el cielo está más cubierto."""

		factor_nubosidad = self.nubosidad / 100.0
		gris_azulado = (118, 122, 132)
		gris_melocoton = (164, 154, 148)

		self.color_superior = desaturar_color(
			interpolar_color_base(INDIGO_PROFUNDO, gris_azulado, factor_nubosidad * 0.72),
			factor_nubosidad * 0.34,
		)
		self.color_inferior = desaturar_color(
			interpolar_color_base(MELCOCO_TIBIO, gris_melocoton, factor_nubosidad * 0.82),
			factor_nubosidad * 0.42,
		)

	def dibujar(self, superficie):
		for y in range(self.alto):
			progreso = y / max(1, self.alto - 1)
			color = interpolar_color(self.color_superior, self.color_inferior, progreso)
			pygame.draw.line(superficie, color, (0, y), (self.ancho, y))


class FondoDia:
	"""Dibuja un cielo pastel de día con un sol difuminado en la esquina."""

	def __init__(self, ancho, alto):
		self.ancho = ancho
		self.alto = alto
		self.color_superior = CELESTE_PASTEL
		self.color_inferior = BLANCO_SUAVE
		self.sol_surface, self.sol_rect = self._crear_sol()

	def _crear_sol(self):
		"""Crea un sol con halo suave usando alpha nativo."""

		tamano = 220
		superficie = pygame.Surface((tamano, tamano), pygame.SRCALPHA)
		centro = (tamano - 56, 56)
		for radio, alpha in [(74, 22), (58, 40), (44, 68), (30, 110)]:
			pygame.draw.circle(superficie, (*SOL_BRILLO, alpha), centro, radio)
		pygame.draw.circle(superficie, (*SOL_BASE, 230), centro, 20)
		return superficie, superficie.get_rect(topleft=(0, 0))

	def dibujar(self, superficie):
		for y in range(self.alto):
			progreso = y / max(1, self.alto - 1)
			color = interpolar_color(self.color_superior, self.color_inferior, progreso)
			pygame.draw.line(superficie, color, (0, y), (self.ancho, y))
		superficie.blit(self.sol_surface, self.sol_rect)


class FondoNoche:
	"""Dibuja el cielo crepuscular nocturno con luna y resplandor."""

	def __init__(self, ancho, alto):
		self.ancho = ancho
		self.alto = alto
		self.color_superior = INDIGO_PROFUNDO
		self.color_inferior = MELCOCO_TIBIO
		self.luna = Luna((self.ancho - 120, 110), 42)

	def dibujar(self, superficie):
		for y in range(self.alto):
			progreso = y / max(1, self.alto - 1)
			color = interpolar_color(self.color_superior, self.color_inferior, progreso)
			pygame.draw.line(superficie, color, (0, y), (self.ancho, y))
		self.luna.dibujar(superficie)


class Luna:
	"""Representa la luna con una capa de resplandor difuminado."""

	def __init__(self, posicion, radio):
		self.x, self.y = posicion
		self.radio = radio
		self.glow_surface, self.glow_rect = self._crear_resplandor()

	def _crear_resplandor(self):
		"""Crea una superficie con alpha para pintar círculos concéntricos."""

		margen = self.radio * 5
		tamano = margen * 2
		superficie = pygame.Surface((tamano, tamano), pygame.SRCALPHA)
		centro = (margen, margen)

		capas = [
			(self.radio + 54, 12),
			(self.radio + 42, 18),
			(self.radio + 30, 28),
			(self.radio + 18, 42),
			(self.radio + 8, 70),
		]

		for radio, alpha in capas:
			pygame.draw.circle(
				superficie,
				(*LUNA_BRILLO, alpha),
				centro,
				radio,
			)

		rect = superficie.get_rect(center=(self.x, self.y))
		return superficie, rect

	def dibujar(self, superficie):
		"""Pinta primero el resplandor y luego el disco principal de la luna."""

		superficie.blit(self.glow_surface, self.glow_rect)
		pygame.draw.circle(superficie, LUNA_BASE, (self.x, self.y), self.radio)
		pygame.draw.circle(superficie, LUNA_BRILLO, (self.x - 6, self.y - 7), self.radio - 7)


class Particle:
	"""Simula una luciérnaga con flotación, vaivén lateral y titileo orgánico."""

	def __init__(self, ancho, alto):
		self.ancho = ancho
		self.alto = alto
		self.tiempo = random.uniform(0, math.tau)
		self.fase_horizontal = random.uniform(0, math.tau)
		self.fase_titileo = random.uniform(0, math.tau)
		self.rapidez_vertical = random.uniform(22.0, 55.0)
		self.amplitud_horizontal = random.uniform(10.0, 28.0)
		self.frecuencia_horizontal = random.uniform(0.7, 1.6)
		self.frecuencia_titileo = random.uniform(2.0, 4.5)
		self.variacion_alpha = random.randint(50, 110)
		self.alpha_base = random.randint(90, 150)
		self.radio = random.randint(2, 4)
		self.color = LUCIERNAGA_NUCLEO
		self.x_base = random.uniform(0, self.ancho)
		self.y = random.uniform(0, self.alto)
		self.sprite = self._crear_sprite()
		self.alpha_actual = self.alpha_base

	def _crear_sprite(self):
		"""Construye una pequeña aura luminosa con soporte nativo de alpha."""

		tamano = self.radio * 8
		superficie = pygame.Surface((tamano, tamano), pygame.SRCALPHA)
		centro = (tamano // 2, tamano // 2)

		capas = [
			(self.radio * 3, (*LUCIERNAGA_AUREOLA, 22)),
			(self.radio * 2, (*LUCIERNAGA_AUREOLA, 60)),
			(self.radio, (*self.color, 220)),
		]

		for radio, color in capas:
			pygame.draw.circle(superficie, color, centro, radio)

		return superficie

	def reiniciar_abajo(self):
		"""Reaparece en la parte inferior cuando sale por arriba de la pantalla."""

		self.x_base = random.uniform(0, self.ancho)
		self.y = self.alto + random.uniform(5, 45)
		self.tiempo = random.uniform(0, math.tau)
		self.fase_horizontal = random.uniform(0, math.tau)
		self.fase_titileo = random.uniform(0, math.tau)

	def actualizar(self, delta_tiempo):
		"""Actualiza la posición y la intensidad luminosa con movimiento continuo."""

		self.tiempo += delta_tiempo
		self.y -= self.rapidez_vertical * delta_tiempo

		if self.y < -15:
			self.reiniciar_abajo()

		oscilacion = math.sin(self.tiempo * self.frecuencia_horizontal + self.fase_horizontal)
		self.x = self.x_base + oscilacion * self.amplitud_horizontal

		pulso = math.sin(self.tiempo * self.frecuencia_titileo + self.fase_titileo)
		intensidad = self.alpha_base + int(self.variacion_alpha * pulso)
		self.alpha_actual = max(0, min(255, intensidad))

	def dibujar(self, superficie):
		"""Dibuja la luciérnaga aplicando un alpha global sobre su sprite."""

		sprite = self.sprite.copy()
		sprite.set_alpha(self.alpha_actual)
		rect = sprite.get_rect(center=(int(self.x), int(self.y)))
		superficie.blit(sprite, rect)


class Petalo:
	"""Partícula de día que cae suavemente como pétalo rosado."""

	def __init__(self, ancho, alto):
		self.ancho = ancho
		self.alto = alto
		self.x = random.uniform(0, self.ancho)
		self.y = random.uniform(-self.alto, 0)
		self.velocidad_caida = random.uniform(18.0, 42.0)
		self.ondulacion = random.uniform(0.8, 2.2)
		self.fase = random.uniform(0, math.tau)
		self.tamano = random.randint(4, 7)
		self.alpha = random.randint(120, 190)

	def actualizar(self, delta_tiempo):
		"""Desciende con una deriva lateral suave y reaparece arriba."""

		self.y += self.velocidad_caida * delta_tiempo
		self.x += math.sin((self.y * 0.018) + self.fase) * self.ondulacion
		if self.y > self.alto + 16:
			self.y = random.uniform(-40, -8)
			self.x = random.uniform(0, self.ancho)

	def dibujar(self, superficie):
		"""Pinta un pétalo sutil con transparencia variable."""

		superficie_petalo = pygame.Surface((self.tamano * 4, self.tamano * 3), pygame.SRCALPHA)
		pygame.draw.ellipse(
			superficie_petalo,
			(255, 204, 220, self.alpha),
			pygame.Rect(0, 0, self.tamano * 4, self.tamano * 2),
		)
		rect = superficie_petalo.get_rect(center=(int(self.x), int(self.y)))
		superficie.blit(superficie_petalo, rect)


class Luciernaga:
	"""Partícula nocturna original que flota hacia arriba y titila."""

	def __init__(self, ancho, alto):
		self.ancho = ancho
		self.alto = alto
		self.tiempo = random.uniform(0, math.tau)
		self.fase_horizontal = random.uniform(0, math.tau)
		self.fase_titileo = random.uniform(0, math.tau)
		self.rapidez_vertical = random.uniform(22.0, 55.0)
		self.amplitud_horizontal = random.uniform(10.0, 28.0)
		self.frecuencia_horizontal = random.uniform(0.7, 1.6)
		self.frecuencia_titileo = random.uniform(2.0, 4.5)
		self.variacion_alpha = random.randint(50, 110)
		self.alpha_base = random.randint(90, 150)
		self.radio = random.randint(2, 4)
		self.color = LUCIERNAGA_NUCLEO
		self.x_base = random.uniform(0, self.ancho)
		self.y = random.uniform(0, self.alto)
		self.sprite = self._crear_sprite()
		self.alpha_actual = self.alpha_base

	def _crear_sprite(self):
		"""Construye una pequeña aura luminosa con soporte nativo de alpha."""

		tamano = self.radio * 8
		superficie = pygame.Surface((tamano, tamano), pygame.SRCALPHA)
		centro = (tamano // 2, tamano // 2)

		capas = [
			(self.radio * 3, (*LUCIERNAGA_AUREOLA, 22)),
			(self.radio * 2, (*LUCIERNAGA_AUREOLA, 60)),
			(self.radio, (*self.color, 220)),
		]

		for radio, color in capas:
			pygame.draw.circle(superficie, color, centro, radio)

		return superficie

	def reiniciar_abajo(self):
		"""Reaparece en la parte inferior cuando sale por arriba de la pantalla."""

		self.x_base = random.uniform(0, self.ancho)
		self.y = self.alto + random.uniform(5, 45)
		self.tiempo = random.uniform(0, math.tau)
		self.fase_horizontal = random.uniform(0, math.tau)
		self.fase_titileo = random.uniform(0, math.tau)

	def actualizar(self, delta_tiempo):
		"""Actualiza la posición y la intensidad luminosa con movimiento continuo."""

		self.tiempo += delta_tiempo
		self.y -= self.rapidez_vertical * delta_tiempo

		if self.y < -15:
			self.reiniciar_abajo()

		oscilacion = math.sin(self.tiempo * self.frecuencia_horizontal + self.fase_horizontal)
		self.x = self.x_base + oscilacion * self.amplitud_horizontal

		pulso = math.sin(self.tiempo * self.frecuencia_titileo + self.fase_titileo)
		intensidad = self.alpha_base + int(self.variacion_alpha * pulso)
		self.alpha_actual = max(0, min(255, intensidad))

	def dibujar(self, superficie):
		"""Dibuja la luciérnaga aplicando un alpha global sobre su sprite."""

		sprite = self.sprite.copy()
		sprite.set_alpha(self.alpha_actual)
		rect = sprite.get_rect(center=(int(self.x), int(self.y)))
		superficie.blit(sprite, rect)


class SwitchAtmosferico:
	"""Interruptor visual tipo iOS/macOS para alternar entre día y noche."""

	def __init__(self, x, y, ancho=84, alto=34):
		self.rect = pygame.Rect(x, y, ancho, alto)
		self.radio = alto // 2

	def contiene(self, posicion):
		"""Indica si un clic ocurrió dentro del interruptor."""

		return self.rect.collidepoint(posicion)

	def dibujar(self, superficie, modo):
		"""Renderiza el track, la perilla y una etiqueta sutil del modo activo."""

		es_activo = modo == MODO_DIA
		color_track = (188, 219, 245) if es_activo else (80, 84, 110)
		color_perilla = (255, 255, 255) if es_activo else (238, 233, 208)
		color_borde = (255, 255, 255, 54) if es_activo else (255, 246, 214, 34)

		superficie_track = pygame.Surface(self.rect.size, pygame.SRCALPHA)
		pygame.draw.rect(superficie_track, (*color_track, 220), superficie_track.get_rect(), border_radius=self.radio)
		pygame.draw.rect(superficie_track, color_borde, superficie_track.get_rect(), width=1, border_radius=self.radio)

		knob_diametro = self.rect.height - 6
		knob_x = 3 if es_activo else self.rect.width - knob_diametro - 3
		knob_rect = pygame.Rect(knob_x, 3, knob_diametro, knob_diametro)
		pygame.draw.ellipse(superficie_track, color_perilla, knob_rect)
		pygame.draw.ellipse(superficie_track, (255, 255, 255, 90), knob_rect.inflate(-6, -6), 1)

		superficie.blit(superficie_track, self.rect)

		fuente = pygame.font.Font(None, 18)
		texto = fuente.render("DIA" if es_activo else "NOCHE", True, (255, 255, 255))
		texto.set_alpha(170)
		rect_texto = texto.get_rect(midleft=(self.rect.right + 10, self.rect.centery))
		superficie.blit(texto, rect_texto)


class Tulip:
	"""Representa un tulipán sobre la colina con balanceo orgánico y fecha visible."""

	def __init__(self, x, y_base, scale, datos_dia, dia, temp_min, temp_max, height):
		self.x = float(x)
		self.y_base = float(y_base)
		self.scale = float(scale)
		self.datos_dia = datos_dia
		self.dia = int(dia)
		self.colores = calcular_paleta_por_temperatura(
			self.datos_dia["temp_media"],
			temp_min,
			temp_max,
		)
		self.height = float(height)
		self.altura_tallo = self.height
		self.ancho_capullo = 44 * self.scale
		self.alto_capullo = 58 * self.scale
		self.grosor_tallo = max(1, int(self.colores["grosor_tallo"] * self.scale))
		self.sway_offset = random.uniform(0.0, math.tau)
		self.sway_speed = random.uniform(0.65, 1.35)
		self.sway_amplitude = random.uniform(5.5, 13.5) * self.scale

	def _puntos_bezier(self, inicio, control, fin, segmentos=18):
		"""Aproxima una curva Bézier cuadrática con segmentos rectos pequeños."""

		puntos = []
		for indice in range(segmentos + 1):
			t = indice / segmentos
			inverso = 1 - t
			x = inverso * inverso * inicio[0] + 2 * inverso * t * control[0] + t * t * fin[0]
			y = inverso * inverso * inicio[1] + 2 * inverso * t * control[1] + t * t * fin[1]
			puntos.append((x, y))
		return puntos

	def _desplazamiento_viento(self, tiempo_viento):
		"""Calcula el balanceo del tulipán de forma asincrónica y natural."""

		return math.sin(tiempo_viento * self.sway_speed + self.sway_offset) * self.sway_amplitude

	def _dibujar_tallo(self, superficie, tiempo_viento):
		"""Dibuja el tallo como una curva estilizada y ligeramente ondulada."""

		desplazamiento = self._desplazamiento_viento(tiempo_viento)
		inicio = (self.x, self.y_base)
		control = (
			self.x + desplazamiento * 0.30,
			self.y_base - self.altura_tallo * 0.52,
		)
		fin = (
			self.x + desplazamiento * 0.78,
			self.y_base - self.altura_tallo,
		)
		puntos = [(int(x), int(y)) for x, y in self._puntos_bezier(inicio, control, fin)]

		pygame.draw.lines(
			superficie,
			ajustar_brillo(self.colores["tallo"], 0.82),
			False,
			puntos,
			self.grosor_tallo + 2,
		)
		pygame.draw.lines(
			superficie,
			self.colores["tallo"],
			False,
			puntos,
			self.grosor_tallo,
		)

		return fin, desplazamiento

	def _dibujar_capullo(self, superficie, posicion_capullo):
		"""Construye el capullo con tres elipses superpuestas para dar volumen."""

		x_centro, y_centro = posicion_capullo
		ancho = max(12, int(self.ancho_capullo))
		alto = max(16, int(self.alto_capullo))
		superficie_capullo = pygame.Surface((ancho + 12, alto + 12), pygame.SRCALPHA)

		rect_izquierdo = pygame.Rect(2, 4, int(ancho * 0.64), int(alto * 0.82))
		rect_derecho = pygame.Rect(int(ancho * 0.34), 4, int(ancho * 0.64), int(alto * 0.82))
		rect_central = pygame.Rect(int(ancho * 0.18), 0, int(ancho * 0.70), int(alto * 0.98))

		pygame.draw.ellipse(superficie_capullo, self.colores["petalo_izq"], rect_izquierdo)
		pygame.draw.ellipse(superficie_capullo, self.colores["petalo_der"], rect_derecho)
		pygame.draw.ellipse(superficie_capullo, self.colores["petalo_centro"], rect_central)

		rect_capullo = superficie_capullo.get_rect(center=(int(x_centro), int(y_centro)))
		superficie.blit(superficie_capullo, rect_capullo)

	def _dibujar_numero(self, superficie, fuente, posicion_capullo):
		"""Dibuja el número del día arriba del capullo con sutil transparencia."""

		texto = fuente.render(str(self.dia), True, (245, 240, 232))
		texto.set_alpha(168)
		sombra = fuente.render(str(self.dia), True, (52, 44, 58))
		sombra.set_alpha(60)
		rect = texto.get_rect(midbottom=(int(posicion_capullo[0]), int(posicion_capullo[1] - self.alto_capullo * 0.84)))
		rect_sombra = rect.move(1, 1)
		superficie.blit(sombra, rect_sombra)
		superficie.blit(texto, rect)

	def dibujar(self, superficie, fuente, tiempo_viento):
		"""Dibuja tallo, capullo y número del día siguiendo la oscilación del viento."""

		fin_tallo, desplazamiento = self._dibujar_tallo(superficie, tiempo_viento)
		posicion_capullo = (
			fin_tallo[0] + desplazamiento * 0.16,
			fin_tallo[1] - self.alto_capullo * 0.36,
		)
		self._dibujar_capullo(superficie, posicion_capullo)
		self._dibujar_numero(superficie, fuente, posicion_capullo)


class Colina:
	"""Genera una capa de terreno con curvas suaves basadas en funciones senoidales."""

	def __init__(self, ancho, alto, base_y, amplitud, frecuencia, fase, color, paso_x=8):
		self.ancho = ancho
		self.alto = alto
		self.base_y = base_y
		self.amplitud = amplitud
		self.frecuencia = frecuencia
		self.fase = fase
		self.color = color
		self.paso_x = paso_x
		self.puntos = self._generar_puntos()

	def _altura_en_x(self, x):
		"""Combina dos ondas suaves para dar una silueta más orgánica."""

		curva_principal = math.sin((x * self.frecuencia) + self.fase) * self.amplitud
		curva_secundaria = math.sin((x * self.frecuencia * 0.52) + self.fase * 1.7) * (self.amplitud * 0.22)
		retorno_suave = math.sin((x * self.frecuencia * 0.18) + self.fase * 0.3) * (self.amplitud * 0.08)
		return self.base_y + curva_principal + curva_secundaria + retorno_suave

	def y_en_x(self, x):
		"""Expone la altura de la colina para situar objetos encima de la superficie."""

		return self._altura_en_x(x)

	def _generar_puntos(self):
		"""Calcula la polilínea superior de la colina y cierra la forma hasta el fondo."""

		puntos = []
		for x in range(0, self.ancho + self.paso_x, self.paso_x):
			y = self._altura_en_x(x)
			y = max(0, min(self.alto, y))
			puntos.append((x, int(y)))

		puntos.append((self.ancho, self.alto))
		puntos.append((0, self.alto))
		return puntos

	def dibujar(self, superficie):
		"""Renderiza la colina como un polígono sólido que cubre hasta el borde inferior."""

		pygame.draw.polygon(superficie, self.color, self.puntos)


class CapaColinaCalendario:
	"""Agrupa una colina y los tulipanes cronológicos que crecen sobre ella."""

	def __init__(self, colina, dia_inicio, dia_fin, escala, offset_vertical, altura_min, altura_max, datos_mes, temp_min, temp_max, fuente):
		self.colina = colina
		self.dia_inicio = dia_inicio
		self.dia_fin = dia_fin
		self.escala = escala
		self.offset_vertical = offset_vertical
		self.altura_min = altura_min
		self.altura_max = altura_max
		self.datos_mes = datos_mes
		self.temp_min = temp_min
		self.temp_max = temp_max
		self.fuente = fuente
		self.tulipanes = self._crear_tulipanes()

	def _crear_tulipanes(self):
		"""Distribuye los días en orden de izquierda a derecha sobre la colina asignada."""

		tulipanes = []
		cantidad = self.dia_fin - self.dia_inicio + 1
		margen = 58
		extension = ANCHO - (margen * 2)

		for indice, dia in enumerate(range(self.dia_inicio, self.dia_fin + 1)):
			progreso = 0.5 if cantidad == 1 else indice / (cantidad - 1)
			x = margen + (extension * progreso)
			y_base = self.colina.y_en_x(x) - self.offset_vertical
			tulipanes.append(
				Tulip(
					x=x,
					y_base=y_base,
					scale=self.escala,
					datos_dia=self.datos_mes[dia - 1],
					dia=dia,
					temp_min=self.temp_min,
					temp_max=self.temp_max,
					height=random.uniform(self.altura_min, self.altura_max),
				)
			)

		return tulipanes

	def dibujar(self, superficie, tiempo_viento):
		"""Dibuja primero la colina y luego los tulipanes que le corresponden."""

		self.colina.dibujar(superficie)
		for tulipan in self.tulipanes:
			tulipan.dibujar(superficie, self.fuente, tiempo_viento)


class JardinBase:
	"""Encapsula la ventana, el bucle principal y todos los elementos base."""

	def __init__(self):
		self.datos_mes = get_mock_month_data()
		self.temp_min = min(registro["temp_media"] for registro in self.datos_mes)
		self.temp_max = max(registro["temp_media"] for registro in self.datos_mes)
		self.humedad_promedio = sum(registro["humedad"] for registro in self.datos_mes) / len(self.datos_mes)
		pygame.init()
		pygame.display.set_caption("Pradera Climática Cronológica")
		self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
		self.reloj = pygame.time.Clock()
		self.ejecutando = True
		self.fuente_numero = pygame.font.Font(None, 18)

		self.modo_actual = MODO_NOCHE
		self.fondo_dia = FondoDia(ANCHO, ALTO)
		self.fondo_noche = FondoNoche(ANCHO, ALTO)
		self.switch = SwitchAtmosferico(22, 22)
		self.petalos_dia = [Petalo(ANCHO, ALTO) for _ in range(NUMERO_PARTICULAS)]
		self.luciernagas_noche = [Luciernaga(ANCHO, ALTO) for _ in range(NUMERO_PARTICULAS)]
		self.capas_terreno = self._crear_capas_terreno()
		self.tiempo_viento = 0.0

	def _modo_activo(self):
		"""Devuelve el modo atmosférico actual."""

		return self.modo_actual

	def _crear_capas_terreno(self):
		"""Prepara las tres colinas originales y distribuye los 31 días por tramos."""

		configuraciones = [
			{
				"colina": Colina(ANCHO, ALTO, 350, 28, 0.0065, 0.8, COLINA_FONDO, 8),
				"dias": (22, 31),
				"escala": 0.5,
				"offset_vertical": 4,
				"altura_min": 100,
				"altura_max": 130,
			},
			{
				"colina": Colina(ANCHO, ALTO, 425, 40, 0.0082, 2.1, COLINA_MEDIA, 8),
				"dias": (12, 21),
				"escala": 0.75,
				"offset_vertical": 3,
				"altura_min": 65,
				"altura_max": 85,
			},
			{
				"colina": Colina(ANCHO, ALTO, 505, 52, 0.0105, 3.4, COLINA_FRENTE, 8),
				"dias": (1, 11),
				"escala": 1.10,
				"offset_vertical": 2,
				"altura_min": 35,
				"altura_max": 50,
			},
		]

		capas = []
		for configuracion in configuraciones:
			capas.append(
				CapaColinaCalendario(
					colina=configuracion["colina"],
					dia_inicio=configuracion["dias"][0],
					dia_fin=configuracion["dias"][1],
					escala=configuracion["escala"],
					offset_vertical=configuracion["offset_vertical"],
					altura_min=configuracion["altura_min"],
					altura_max=configuracion["altura_max"],
					datos_mes=self.datos_mes,
					temp_min=self.temp_min,
					temp_max=self.temp_max,
					fuente=self.fuente_numero,
				)
			)

		return capas

	def manejar_eventos(self):
		"""Gestiona el cierre de la ventana y la tecla ESC."""

		for evento in pygame.event.get():
			if evento.type == pygame.QUIT:
				self.ejecutando = False
			elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
				if self.switch.contiene(evento.pos):
					self.modo_actual = MODO_DIA if self.modo_actual == MODO_NOCHE else MODO_NOCHE
			elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
				self.ejecutando = False

	def actualizar(self, delta_tiempo):
		"""Actualiza únicamente las partículas del modo atmosférico activo."""

		self.tiempo_viento = pygame.time.get_ticks() / 1000.0
		if self.modo_actual == MODO_DIA:
			for particula in self.petalos_dia:
				particula.actualizar(delta_tiempo)
		else:
			for particula in self.luciernagas_noche:
				particula.actualizar(delta_tiempo)

	def dibujar(self):
		"""Compone la escena en orden: atmósfera, colinas, tulipanes, partículas y switch."""

		if self.modo_actual == MODO_DIA:
			self.fondo_dia.dibujar(self.pantalla)
		else:
			self.fondo_noche.dibujar(self.pantalla)

		for capa in self.capas_terreno:
			capa.dibujar(self.pantalla, self.tiempo_viento)

		if self.modo_actual == MODO_DIA:
			for particula in self.petalos_dia:
				particula.dibujar(self.pantalla)
		else:
			for particula in self.luciernagas_noche:
				particula.dibujar(self.pantalla)

		self.switch.dibujar(self.pantalla, self.modo_actual)

		pygame.display.flip()

	def ejecutar(self):
		"""Bucle principal limitado a 60 FPS estables."""

		while self.ejecutando:
			delta_tiempo = self.reloj.tick(FPS) / 1000.0
			self.manejar_eventos()
			self.actualizar(delta_tiempo)
			self.dibujar()

		pygame.quit()
		sys.exit()


def main():
	"""Punto de entrada del script."""

	JardinBase().ejecutar()


if __name__ == "__main__":
	main()

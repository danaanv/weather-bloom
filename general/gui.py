"""Funciones y widgets de interfaz para la escena del jardín climático."""

import pygame

from database import load_latest_day_data, load_monthly_weather_data
from entities import Colina, Particle, Tulip

ANCHO = 1000
ALTO = 650
FPS = 60
NUMERO_PARTICULAS = 70
NUMERO_TULIPANES_FONDO = 10
NUMERO_TULIPANES_MEDIO = 13
NUMERO_TULIPANES_FRENTE = 16

MODO_DIA = "dia"
MODO_NOCHE = "noche"

INDIGO_PROFUNDO = (22, 26, 67)
MELCOCO_TIBIO = (255, 196, 166)
CELESTE_PASTEL = (187, 226, 248)
BLANCO_SUAVE = (248, 250, 255)
LUNA_BASE = (244, 236, 205)
LUNA_BRILLO = (255, 248, 224)
SOL_BASE = (255, 232, 170)
SOL_BRILLO = (255, 246, 214)


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
			pygame.draw.circle(superficie, (*LUNA_BRILLO, alpha), centro, radio)

		rect = superficie.get_rect(center=(self.x, self.y))
		return superficie, rect

	def dibujar(self, superficie):
		"""Pinta primero el resplandor y luego el disco principal de la luna."""

		superficie.blit(self.glow_surface, self.glow_rect)
		pygame.draw.circle(superficie, LUNA_BASE, (self.x, self.y), self.radio)
		pygame.draw.circle(superficie, LUNA_BRILLO, (self.x - 6, self.y - 7), self.radio - 7)


def limitar_valor(valor, minimo, maximo):
	"""Recorta un valor numérico para mantenerlo dentro de un rango seguro."""

	return max(minimo, min(maximo, valor))


def interpolar_color(color_superior, color_inferior, progreso):
	"""Interpola dos colores RGB en función de un progreso entre 0 y 1."""

	return tuple(
		int(color_superior[i] + (color_inferior[i] - color_superior[i]) * progreso)
		for i in range(3)
	)


class FondoDia:
	"""Dibuja un cielo pastel de día con un sol difuminado en la esquina."""

	def __init__(self, ancho=ANCHO, alto=ALTO):
		self.ancho = ancho
		self.alto = alto
		self.color_superior = CELESTE_PASTEL
		self.color_inferior = BLANCO_SUAVE
		self.sol_surface, self.sol_rect = self._crear_sol()

	def _crear_sol(self):
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

	def __init__(self, ancho=ANCHO, alto=ALTO):
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


class SwitchAtmosferico:
	"""Interruptor visual tipo iOS/macOS para alternar entre día y noche."""

	def __init__(self, x, y, ancho=84, alto=34):
		self.rect = pygame.Rect(x, y, ancho, alto)
		self.radio = alto // 2

	def contiene(self, posicion):
		return self.rect.collidepoint(posicion)

	def dibujar(self, superficie, modo):
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


class PanelInformativo:
	"""Muestra el último registro climático en un panel limpio y legible."""

	def __init__(self, ancho=ANCHO, alto=ALTO, fuente_titulo=None, fuente_texto=None):
		self.rect = pygame.Rect(ancho - 300, 150, 268, 140)
		self.fuente_titulo = fuente_titulo or pygame.font.Font(None, 20)
		self.fuente_texto = fuente_texto or pygame.font.Font(None, 18)

	def dibujar(self, superficie, registro):
		superficie_panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
		pygame.draw.rect(superficie_panel, (18, 22, 34, 155), superficie_panel.get_rect(), border_radius=18)
		pygame.draw.rect(superficie_panel, (255, 255, 255, 42), superficie_panel.get_rect(), width=1, border_radius=18)

		titulo = self.fuente_titulo.render(
			f"Última actualización: {registro.get('fecha') or 'Sin datos'}",
			True,
			(245, 245, 248),
		)
		titulo.set_alpha(230)
		superficie_panel.blit(titulo, (14, 12))

		lineas = [
			f"Temperatura Media: {float(registro.get('temp_media', 0.0)):.1f} °C",
			f"Humedad: {float(registro.get('humedad', 0.0)):.1f} %",
			f"Viento Máximo: {float(registro.get('viento_max', 0.0)):.1f} km/h",
			f"Precipitación: {float(registro.get('precipitacion', 0.0)):.1f} mm",
		]

		y = 38
		for linea in lineas:
			texto = self.fuente_texto.render(linea, True, (230, 233, 238))
			texto.set_alpha(210)
			superficie_panel.blit(texto, (14, y))
			y += 24

		superficie.blit(superficie_panel, self.rect)


COLINA_FONDO = (28, 40, 72)
COLINA_MEDIA = (20, 74, 80)
COLINA_FRENTE = (18, 58, 34)


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
					height=__import__("random").uniform(self.altura_min, self.altura_max),
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
		pygame.init()
		pygame.display.set_caption("Pradera Climática Modular")
		self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
		self.datos_mes = load_monthly_weather_data()
		self.dato_mas_reciente = load_latest_day_data()
		self.temp_min = min(registro["temp_media"] for registro in self.datos_mes)
		self.temp_max = max(registro["temp_media"] for registro in self.datos_mes)
		self.humedad_promedio = sum(registro["humedad"] for registro in self.datos_mes) / len(self.datos_mes)

		self.modo_actual = MODO_NOCHE
		self.fondo_dia = FondoDia(ANCHO, ALTO)
		self.fondo_noche = FondoNoche(ANCHO, ALTO)
		self.switch = SwitchAtmosferico(22, 22)
		self.panel_informativo = PanelInformativo(
			ANCHO,
			ALTO,
			pygame.font.Font(None, 20),
			pygame.font.Font(None, 18),
		)
		self.petalos_dia = [Particle(ANCHO, ALTO, modo="dia") for _ in range(NUMERO_PARTICULAS)]
		self.luciernagas_noche = [Particle(ANCHO, ALTO, modo="noche") for _ in range(NUMERO_PARTICULAS)]
		self.capas_terreno = self._crear_capas_terreno()
		self.tiempo_viento = 0.0
		self.reloj = pygame.time.Clock()
		self.ejecutando = True

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
					fuente=pygame.font.Font(None, 18),
				)
			)

		return capas

	def manejar_eventos(self):
		"""Gestiona el cierre de la ventana, el switch y la tecla ESC."""

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
		"""Compone la escena en orden: atmósfera, colinas, tulipanes, panel, partículas y switch."""

		if self.modo_actual == MODO_DIA:
			self.fondo_dia.dibujar(self.pantalla)
		else:
			self.fondo_noche.dibujar(self.pantalla)

		for capa in self.capas_terreno:
			capa.dibujar(self.pantalla, self.tiempo_viento)

		self.panel_informativo.dibujar(self.pantalla, self.dato_mas_reciente)

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

		self.ejecutando = True
		while self.ejecutando:
			delta_tiempo = self.reloj.tick(FPS) / 1000.0 if hasattr(self, "reloj") else 1 / FPS
			self.manejar_eventos()
			self.actualizar(delta_tiempo)
			self.dibujar()

		pygame.quit()


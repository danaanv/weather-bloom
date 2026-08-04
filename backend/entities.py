"""Entidades visuales independientes: colinas, tulipanes y partículas."""

import math
import random

import pygame


def limitar_valor(valor, minimo, maximo):
	"""Recorta un valor numérico para mantenerlo dentro de un rango seguro."""

	return max(minimo, min(maximo, valor))


def lerp(valor_inicial, valor_final, factor):
	"""Interpola linealmente dos valores numéricos."""

	factor = limitar_valor(factor, 0.0, 1.0)
	return valor_inicial + (valor_final - valor_inicial) * factor


def lerp_color(color_inicial, color_final, factor):
	"""Interpola dos colores RGB canal por canal."""

	factor = limitar_valor(factor, 0.0, 1.0)
	return tuple(int(lerp(color_inicial[i], color_final[i], factor)) for i in range(3))


def ajustar_brillo(color, factor):
	"""Aclara u oscurece un color RGB multiplicando cada canal por un factor."""

	return tuple(max(0, min(255, int(canal * factor))) for canal in color)


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


class Particle:
	"""Partícula adaptable: luciérnaga en noche o pétalo en día."""

	def __init__(self, ancho, alto, modo="noche"):
		self.ancho = ancho
		self.alto = alto
		self.modo = modo
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
		self.color = (255, 245, 160)
		self.x_base = random.uniform(0, self.ancho)
		self.y = random.uniform(0, self.alto)
		self.sprite = self._crear_sprite()
		self.alpha_actual = self.alpha_base

	def _crear_sprite(self):
		"""Construye una pequeña aura luminosa con soporte nativo de alpha."""

		tamano = self.radio * 8
		superficie = pygame.Surface((tamano, tamano), pygame.SRCALPHA)
		centro = (tamano // 2, tamano // 2)

		if self.modo == "dia":
			pygame.draw.ellipse(superficie, (255, 204, 220, 210), pygame.Rect(0, 0, tamano, tamano // 2))
		else:
			capas = [
				(self.radio * 3, (255, 214, 95, 22)),
				(self.radio * 2, (255, 214, 95, 60)),
				(self.radio, (255, 245, 160, 220)),
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
		if self.modo == "dia":
			self.y += self.rapidez_vertical * 0.7 * delta_tiempo
			self.x = self.x_base + math.sin(self.tiempo * self.frecuencia_horizontal + self.fase_horizontal) * self.amplitud_horizontal * 0.45
			if self.y > self.alto + 20:
				self.y = random.uniform(-30, -5)
				self.x_base = random.uniform(0, self.ancho)
		else:
			self.y -= self.rapidez_vertical * delta_tiempo
			if self.y < -15:
				self.reiniciar_abajo()
			oscilacion = math.sin(self.tiempo * self.frecuencia_horizontal + self.fase_horizontal)
			self.x = self.x_base + oscilacion * self.amplitud_horizontal

		pulso = math.sin(self.tiempo * self.frecuencia_titileo + self.fase_titileo)
		intensidad = self.alpha_base + int(self.variacion_alpha * pulso)
		self.alpha_actual = max(0, min(255, intensidad))

	def dibujar(self, superficie):
		"""Dibuja la partícula aplicando alpha sobre su sprite."""

		sprite = self.sprite.copy()
		sprite.set_alpha(self.alpha_actual)
		rect = sprite.get_rect(center=(int(self.x), int(self.y)))
		superficie.blit(sprite, rect)


class Tulip:
	"""Representa un tulipán sobre la colina con balanceo orgánico y fecha visible."""

	def __init__(self, x, y_base, scale, datos_dia, dia, temp_min, temp_max, height):
		self.x = float(x)
		self.y_base = float(y_base)
		self.scale = float(scale)
		self.datos_dia = datos_dia
		self.dia = int(dia)
		self.colores = calcular_paleta_por_temperatura(self.datos_dia["temp_media"], temp_min, temp_max)
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
		control = (self.x + desplazamiento * 0.30, self.y_base - self.altura_tallo * 0.52)
		fin = (self.x + desplazamiento * 0.78, self.y_base - self.altura_tallo)
		puntos = [(int(x), int(y)) for x, y in self._puntos_bezier(inicio, control, fin)]

		pygame.draw.lines(superficie, ajustar_brillo(self.colores["tallo"], 0.82), False, puntos, self.grosor_tallo + 2)
		pygame.draw.lines(superficie, self.colores["tallo"], False, puntos, self.grosor_tallo)

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
		posicion_capullo = (fin_tallo[0] + desplazamiento * 0.16, fin_tallo[1] - self.alto_capullo * 0.36)
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
		extension = 1000 - (margen * 2)

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

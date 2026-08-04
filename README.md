# Weather Bloom

Weather Bloom es una escena interactiva en Pygame que convierte datos climáticos de PostgreSQL en un jardín visual con tulipanes, colinas matemáticas y modos atmosféricos de día y noche.

## Estructura principal

- `general/main.py`: punto de entrada mínimo.
- `general/gui.py`: fondos, switch día/noche, panel informativo y composición visual.
- `general/database.py`: conexión a PostgreSQL, consultas SQL y fallback a datos mock.
- `general/entities.py`: entidades gráficas como colinas, tulipanes y partículas.
- `general/requirements.txt`: dependencias del entorno visual.
- `docs/design-notes.md`: notas de diseño del proyecto.

## Requisitos

- Python 3.8 o superior.
- `pygame`
- `psycopg2`
- PostgreSQL con una tabla llamada `clima`.

## Instalación

Desde la raíz del proyecto:

```bash
pip install -r general/requirements.txt
```

## Ejecución

La forma más directa de ejecutar la aplicación es entrar a la carpeta `general` y correr el entrypoint:

```bash
cd general
python main.py
```

Si prefieres lanzarlo desde la raíz, usa el mismo intérprete pero conservando la carpeta `general` como directorio de trabajo.

## Variables de entorno

La conexión a PostgreSQL utiliza estas variables:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASS`

Si no se definen, se usan valores por defecto orientados a desarrollo local.

## Controles

- Clic en el switch: alterna entre modo día y modo noche.
- `ESC`: cierra la ventana.
- Botón de cierre de la ventana: cierra la aplicación.

## Comportamiento de respaldo

Si PostgreSQL no responde o la tabla `clima` no contiene datos suficientes, la aplicación carga un mes simulado para que la escena siga funcionando sin interrupciones.

## Notas de implementación

- La escena corre a 60 FPS.
- La lógica está separada en módulos para mantener `main.py` corto.
- Los tulipanes se ordenan cronológicamente y su color depende de la temperatura media del día.
- El panel superior muestra el último día registrado con sus métricas climáticas.

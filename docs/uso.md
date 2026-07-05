# Uso

## Iniciar una sesión

```bash
cd poc
.venv/bin/python3 main.py [--asignatura "Nombre"] [--profesor "Nombre"]
```

O, con el alias `clase` (ver [instalación](instalacion.md#alias-rápido-para-clase)):

```bash
clase --asignatura "Desarrollo de Software II" --profesor "Calonzo"
```

Ambos flags son opcionales. Van al frontmatter de la nota final y `--asignatura` además se usa (slugificado) en el nombre del archivo. Fecha y hora se toman automáticamente del momento de inicio.

## Durante la sesión

La consola muestra en vivo:

- `[main] modelo cargado, listo para transcribir` — el modelo terminó de cargar, ya está escuchando.
- Una línea por segmento transcrito, con la latencia de inferencia: `[ 1.34s] texto del segmento...`
- `[monitor] cpu=.. mem=.. temp=..` cada 30s (configurable), para seguir el estado térmico.
- Avisos de degradación de modelo o de split de sesión si ocurren (ver [configuración](configuracion.md)).

`Ctrl+C` detiene la captura y cierra la nota de forma prolija. Si el proceso recibe `SIGTERM` (por ejemplo, se cierra la terminal o lo mata systemd) hace lo mismo.

## Salida

Las notas quedan en `poc/sesiones/`, con nombre `clase_<asignatura-slug>_<YYYYMMDD_HHMM>[_parteN].md`. Formato:

````markdown
---
fecha: 2026-06-15
asignatura: Desarrollo de Software II
profesor: Calonzo
duracion: 01:32:14
modelo: faster-whisper-small-int8
---

# Clase — 2026-06-15 09:00

> [!meta]
> - Segmentos: 142
> - Confianza media (avg_logprob): -0.31

## 00:00:12 — 00:00:47
[texto del segmento...]

## 00:00:51 — 00:01:33
[texto del segmento...]
````

Es Markdown estándar con callouts al estilo Obsidian (`> [!meta]`, `> [!warning]`); se ve bien en Obsidian y sigue siendo legible como texto plano en cualquier otro editor.

## Sesiones largas: split automático

Si `OutputConfig.session_split_minutes` está activo (15 min por defecto), la nota se cierra y arranca un archivo nuevo (`_parte2`, `_parte3`, ...) periódicamente, para no perder toda la clase si algo falla cerca del final. Cada parte es una nota completa e independiente.

## Recuperación tras un corte inesperado

Si el proceso muere sin pasar por `Ctrl+C`/`SIGTERM` (corte de luz, kill -9, crash), al arrancar `main.py` de nuevo detecta cualquier `.tmp.md` suelto en `poc/sesiones/` y lo convierte automáticamente en una nota `..._recuperada.md`. Esa nota queda marcada como recuperada y sin la metadata que solo vivía en memoria (asignatura, profesor, duración, modelo) porque no hay forma de reconstruirla.

## Degradación térmica

Si la temperatura de CPU supera el umbral configurado (`ThermalConfig.threshold_c`, 80°C por defecto), el proceso degrada automáticamente el modelo de transcripción a uno más liviano (`ModelConfig.fallback_model_size`) para bajar la carga. Esto es irreversible dentro de una misma sesión (no vuelve a subir de modelo aunque la temperatura baje), a propósito: evita oscilar entre modelos en medio de la clase.

# Instalación

## Requisitos

- Python 3.11+
- Linux con PipeWire o PulseAudio (probado en Pop!_OS). Debería funcionar en cualquier distro con `sounddevice`/PortAudio configurado; no probado en macOS/Windows.
- Micrófono accesible por el sistema de audio.

## Pasos

```bash
cd poc
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Verificá que el micrófono por defecto del sistema sea el que querés usar (`pavucontrol` o el mixer de tu SO). Si necesitás otro dispositivo, ver `AudioConfig.input_device` en [configuración](configuracion.md).

## Primera corrida

```bash
.venv/bin/python3 main.py
```

Debería imprimir `[main] modelo cargado, listo para transcribir` y empezar a mostrar segmentos transcritos a medida que hablás. `Ctrl+C` corta y guarda la nota en `poc/sesiones/`.

> La primera vez que corrés con un tamaño de modelo nuevo, `faster-whisper` lo descarga de Hugging Face (unos cientos de MB para `small`). Necesitás internet para esa descarga única; después la inferencia es 100% local y offline.

## Alias rápido para clase

Si vas a usarlo seguido, conviene un alias en tu `.bashrc`/`.zshrc`:

```bash
alias clase="/ruta/absoluta/a/class-transcription-worke/poc/start_clase.sh"
```

Y después, desde cualquier lado:

```bash
clase --asignatura "Desarrollo de Software II" --profesor "Calonzo"
```

Ver [uso.md](uso.md) para el detalle de los flags y qué genera.

## Problemas comunes

- **`setuptools` / `pkg_resources` al instalar `webrtcvad`**: ya está fijado en `requirements.txt` (`setuptools<81`); si lo instalaste en un venv viejo con una versión más nueva, recreá el venv.
- **No detecta el micrófono / graba silencio**: confirmá el dispositivo por defecto del sistema operativo, no solo el de la app. `python3 -m sounddevice` (con el venv activado) lista los dispositivos disponibles.
- **CPU se calienta / rendimiento cae en clases largas**: es esperado en hardware sin GPU dedicada; ver el monitor térmico en [configuración](configuracion.md#thermalconfig) y las recomendaciones de [hardware y modelos](hardware-y-modelos.md).

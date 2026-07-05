# Documentación

Índice de la documentación del proyecto. Si es tu primera vez acá, seguí el orden sugerido.

1. [Instalación](instalacion.md) — cómo levantar el entorno y correr la PoC.
2. [Uso](uso.md) — cómo iniciar una sesión, flags disponibles, formato de la nota generada.
3. [Configuración](configuracion.md) — referencia de todos los parámetros ajustables en `poc/config.py`.
4. [Hardware y modelos](hardware-y-modelos.md) — qué modelo de Whisper conviene según tu CPU/GPU.
5. [Arquitectura](arquitectura.md) — cómo está organizado el código hoy y hacia dónde evoluciona.
6. [Plan de diseño completo](plan.md) — el documento de diseño original, con el razonamiento detrás de las decisiones técnicas.
7. [Contribuir](contribucion.md) — cómo proponer cambios y qué filosofía sigue el proyecto.

## ¿Qué es esto?

Un *background worker* que graba el micrófono durante una clase, detecta cuándo hay voz (VAD), transcribe esos segmentos con Whisper corriendo 100% local, y arma una nota en Markdown lista para Obsidian. Pensado para no depender de internet ni de servicios pagos, y para correr en hardware modesto (ver [hardware-y-modelos.md](hardware-y-modelos.md)).

El estado actual es una **PoC funcional** en [`poc/`](../poc/) — scripts planos con responsabilidades separadas, no todavía la Clean Architecture descrita en el [plan de diseño](plan.md). La PoC ya es usable día a día; la arquitectura en capas es el siguiente paso cuando el proyecto lo justifique, no un prerrequisito.

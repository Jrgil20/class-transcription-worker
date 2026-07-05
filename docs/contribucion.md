# Contribuir

## Filosofía del proyecto

Este es un *background worker* desatendido: corre solo, sin supervisión, durante una clase entera. Su valor no está en cuántas cosas hace, sino en que **nunca pierde la clase que está grabando**. Un feature nuevo que agrega una falla silenciosa vale menos que ningún feature.

Por eso, antes de sumar una funcionalidad nueva, la pregunta no es "¿estaría bueno tener esto?" sino:

- ¿Hace que el sistema pierda menos audio o notas, o falle de forma más visible cuando algo sale mal?
- ¿O es una funcionalidad nueva que agrega superficie de falla (más dependencias, más estados posibles, más cosas que pueden romperse a mitad de una clase de 90 minutos)?

Si es lo segundo, probablemente no entra en v1, sin importar cuán interesante sea. **No se busca agregar features a lo loco**: cada feature nueva es una apuesta a que el beneficio compensa la robustez que se pierde. En caso de duda, no.

## Qué sí es bienvenido

- Correcciones de bugs, sobre todo los que puedan causar pérdida de audio/notas.
- Mejoras de robustez: manejo de casos borde, recuperación ante fallas, mejor logging de errores.
- Ajustes de configuración/documentación que hagan más fácil instalar y correr esto en otro hardware.
- Optimizaciones de rendimiento que no compliquen la lógica (por ejemplo, un modelo de Whisper más eficiente, ver [hardware-y-modelos.md](hardware-y-modelos.md)).

## Qué pensar dos veces antes de proponer

- Features nuevas que no estén en el [scope de v1](plan.md#no-objetivos-scope-explícito-de-v1) (por ejemplo: diarización por hablante, corrección/resumen con LLM, UI en vivo). No es que nunca vayan a pasar — están explícitamente pateadas a una v2, después de que la base sea sólida.
- Nuevas dependencias que no sean estrictamente necesarias. Cada dependencia nueva es una superficie más grande para que algo falle en una máquina que no es la tuya.
- Abstracciones o refactors "porque va a hacer falta después". Si la PoC no lo necesita hoy, no lo necesita todavía (ver [arquitectura.md](arquitectura.md#hacia-dónde-evoluciona)).
- Cambios que hagan la falla de un componente más silenciosa. Todo error debe loguearse y, si es irrecuperable, debe cortar el proceso guardando lo que haya (no debe quedar corriendo en un estado roto sin avisar).

## Antes de mandar un cambio

1. Probalo con una sesión real de al menos algunos minutos, no solo revisando el código. Este proyecto vive y muere en el comportamiento real con audio, no en la lectura del diff.
2. Si tocaste el pipeline de captura/VAD/transcripción/escritura, verificá explícitamente el camino de error: ¿qué pasa si el micrófono se desconecta a mitad de sesión? ¿Si el proceso muere sin `Ctrl+C`?
3. Si agregás un parámetro configurable, va a [`poc/config.py`](../poc/config.py) con un default sensato, y se documenta en [configuracion.md](configuracion.md).
4. Si agregás o cambiás dependencias, justificá por qué en la descripción del cambio.

## Dudas de scope

Si no estás seguro de si algo encaja en el proyecto, abrí la propuesta como pregunta antes de implementarla. Es más barato discutir el scope antes que revertir código ya escrito.

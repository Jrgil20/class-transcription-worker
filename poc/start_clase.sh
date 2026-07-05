#!/usr/bin/env bash
# Arranca la PoC de transcripción de clases. Ctrl+C para detener y guardar la nota.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
exec .venv/bin/python3 -u main.py "$@"

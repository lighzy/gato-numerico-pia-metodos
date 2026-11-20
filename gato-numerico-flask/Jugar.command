#!/bin/bash
cd "$(dirname "$0")" || exit 1
printf '\nGATO NUMERICO - Mac\n'
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  echo 'Instala Python desde https://www.python.org/downloads/'
  read -r -p 'Presiona Enter para cerrar...' _
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo 'Preparando el juego por primera vez...'
  "$PYTHON" -m venv .venv || { read -r -p 'Presiona Enter para cerrar...' _; exit 1; }
fi
if ! .venv/bin/python -c 'import flask' >/dev/null 2>&1; then
  echo 'Instalando Flask (requiere internet la primera vez)...'
  .venv/bin/python -m pip install -r requirements.txt || { read -r -p 'Presiona Enter para cerrar...' _; exit 1; }
fi
.venv/bin/python iniciar.py
status=$?
if [ "$status" -ne 0 ]; then
  echo 'No se pudo iniciar. Verifica que el puerto 5000 no este ocupado.'
  read -r -p 'Presiona Enter para cerrar...' _
fi
exit "$status"

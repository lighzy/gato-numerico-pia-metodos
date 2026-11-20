@echo off
setlocal
cd /d "%~dp0"
title Gato Numerico
where py >nul 2>nul
if not errorlevel 1 (
  set "PYTHON=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Necesitas instalar Python desde https://www.python.org/downloads/
    echo IMPORTANTE: activa "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
  )
  set "PYTHON=python"
)
if not exist ".venv\Scripts\python.exe" (
  echo Preparando el juego por primera vez...
  %PYTHON% -m venv .venv
  if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -c "import flask" >nul 2>nul
if errorlevel 1 (
  echo Instalando Flask (requiere internet la primera vez)...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto error
)
".venv\Scripts\python.exe" iniciar.py
if errorlevel 1 goto error
exit /b 0
:error
echo.
echo No se pudo iniciar. Comprueba Python, internet y que el puerto 5000 este libre.
pause
exit /b 1

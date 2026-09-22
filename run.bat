@echo off
title Instances UI
cd /d "%~dp0"

:: Verificar si existe entorno virtual y activarlo si aplica
if exist "..\venv\Scripts\activate.bat" (
    call "..\venv\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

:: Verificar si python está disponible
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] No se encontro Python instalado o en el PATH.
    echo Por favor asegurate de tener Python instalado y agregado a las variables de entorno PATH.
    pause
    exit /b 1
)

:: Ejecutar la aplicacion
echo Iniciando instancesIU.py...
python instancesIU.py

:: Si ocurre un error, pausar para que no se cierre la consola de inmediato
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] La aplicacion se cerro con errores (Codigo: %ERRORLEVEL%).
    pause
)

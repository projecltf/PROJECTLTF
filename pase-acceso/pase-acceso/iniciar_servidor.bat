@echo off
title Servidor Pase de Acceso
echo ==================================================
echo  Iniciando Servidor de Pase de Acceso...
echo ==================================================
start "" "http://localhost:3000/acceso"
python "%~dp0server.py"
pause

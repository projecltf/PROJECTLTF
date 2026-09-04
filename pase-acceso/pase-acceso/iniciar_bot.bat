@echo off
title Bot de Discord - Project LTF
echo ==================================================
echo  Iniciando Bot de Discord para Project LTF...
echo ==================================================
python -m pip install -q discord.py
python "%~dp0bot.py"
pause

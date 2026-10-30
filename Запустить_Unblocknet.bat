@echo off
setlocal
cd /d "%~dp0"
title Unblocknet
if exist "%~dp0Unblocknet.exe" (
    start "" "%~dp0Unblocknet.exe" %*
) else (
    start "" "C:\Python314\pythonw.exe" "%~dp0vpn_app.py" %*
)
exit

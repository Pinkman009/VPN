@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0vpn-windows.ps1" -Stop
if errorlevel 1 pause

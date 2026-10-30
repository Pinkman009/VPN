@echo off
setlocal
title VPN - Finland 2053
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0vpn-windows.ps1"
if errorlevel 1 pause

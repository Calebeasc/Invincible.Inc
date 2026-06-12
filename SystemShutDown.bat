@echo off
:: Invincible.Inc — System Shutdown
:: Double-click this file to cleanly stop all Invincible.Inc services.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0SystemShutDown.ps1"

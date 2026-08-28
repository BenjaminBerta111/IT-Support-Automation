@echo off
:: Find the active scheme
powercfg /getactivescheme | findstr /i "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" >nul

:: If it matches High Performance, switch to Balanced. Otherwise, switch to High Performance.
if %errorlevel% equ 0 (
	powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e
        echo Switched to Balanced Mode
) else (
	powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
	echo  Switched to High Performance Mode
)

pause




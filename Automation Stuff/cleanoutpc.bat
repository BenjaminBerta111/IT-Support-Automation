@echo off

echo Cleaning Windows Temporary Files...

del /s /f /q %temp%\*.*

rd /s /q %temp%

md %temp%

echo Flushing Windows DNS Cache...

ipconfig /flushdns


echo Done! Your PC is fresh.
pause
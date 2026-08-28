@echo off
:: 1. Define the folder you want to back up
set "TARGET_BACKUP_DIR=C:\Users\Anon113\Desktop\code-backups"

:: 2. Create a unique timestamp folder name 
set "TIMESTAMP=%date:~10,4%-%date:~4,2%-%date:~7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%"

set "TIMESTAMP=%TIMESTAMP: =0%"

:: 3. Create the new backup directory
set "FINAL_DEST=%TARGET_BACKUP_DIR%\Backup_%TIMESTAMP%"

:: 4. Create the backup folder inside code-backups
mkdir "%FINAL_DEST%" 2>nul

:: 4. Instantly copy all .py and .html files from your folder
echo Backing up Python and HTML files...
xcopy "%~dp0*.py" "%FINAL_DEST%\" /Y /Q >nul

xcopy "%~dp0*.html" "%FINAL_DEST%\" /Y /Q >nul

echo Done! Files saved to Desktop inside AiPNGTuber_Backups. 
timeout /t 1 >nul
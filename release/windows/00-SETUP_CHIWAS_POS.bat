@echo off
setlocal
title CHIWAS POS Setup

if not exist "%~dp0portable-pos\index.html" (
    echo CHIWAS POS files were not found.
    echo Extract the complete ZIP file first, then run this setup again.
    pause
    exit /b 1
)

set "INSTALL_DIR=%LOCALAPPDATA%\Programs\CHIWAS POS"
if not defined LOCALAPPDATA (
    echo Windows did not provide LOCALAPPDATA. Cannot choose a per-user install folder.
    pause
    exit /b 1
)

echo Installing CHIWAS POS for your Windows account...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if errorlevel 1 (
    echo Could not create the install folder:
    echo "%INSTALL_DIR%"
    pause
    exit /b 1
)

xcopy "%~dp0portable-pos" "%INSTALL_DIR%\portable-pos" /E /I /Y >nul
if errorlevel 1 (
    echo Could not copy the POS application files.
    pause
    exit /b 1
)
copy /Y "%~dp0Start_Chiwas_POS_Windows.bat" "%INSTALL_DIR%\Start_Chiwas_POS_Windows.bat" >nul
if errorlevel 1 (
    echo Could not copy the POS launcher.
    pause
    exit /b 1
)
copy /Y "%~dp0Start_Offline_Pos.ps1" "%INSTALL_DIR%\Start_Offline_Pos.ps1" >nul
if errorlevel 1 (
    echo Could not copy the local app server.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$desktop=[Environment]::GetFolderPath('Desktop'); $shell=New-Object -ComObject WScript.Shell; $shortcut=$shell.CreateShortcut((Join-Path $desktop 'CHIWAS POS.lnk')); $shortcut.TargetPath=Join-Path $env:INSTALL_DIR 'Start_Chiwas_POS_Windows.bat'; $shortcut.WorkingDirectory=$env:INSTALL_DIR; $shortcut.Description='CHIWAS LIQUOR STORE & RESTAURANT POS'; $shortcut.Save()"
if errorlevel 1 (
    echo App files are installed, but Windows could not create the desktop shortcut.
    echo You can still launch it from:
    echo "%INSTALL_DIR%\Start_Chiwas_POS_Windows.bat"
    pause
    exit /b 1
)

echo.
echo Setup complete. A CHIWAS POS shortcut is on your Desktop.
echo Starting the POS now. Close its server window to stop the local app.
set "INSTALL_DIR=%INSTALL_DIR%"
start "" "%INSTALL_DIR%\Start_Chiwas_POS_Windows.bat"
exit /b 0

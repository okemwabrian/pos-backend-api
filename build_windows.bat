@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher was not found. Install Python 3.12 or newer from python.org.
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo Node.js 20 or newer is needed to prepare the bundled offline UI assets.
    pause
    exit /b 1
)

if not exist .venv-windows\Scripts\python.exe py -3 -m venv .venv-windows
call .venv-windows\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto :failed
pip install -r requirements-windows.txt
if errorlevel 1 goto :failed
cd mobile
npm install
if errorlevel 1 goto :failed
npm run build
if errorlevel 1 goto :failed
cd ..
node mobile\package_windows.mjs
if errorlevel 1 goto :failed
pyinstaller --noconfirm --clean build_windows.spec
if errorlevel 1 goto :failed

if not exist release\windows mkdir release\windows
copy /y dist\ChiwasLiquorPOS.exe release\windows\ChiwasLiquorPOS.exe >nul
if errorlevel 1 goto :failed

echo.
echo Server build complete: release\windows\ChiwasLiquorPOS.exe
echo Portable offline web build: release\windows\portable-pos\
echo The app creates its database and prompts you to create the owner account on first launch.
pause
exit /b 0

:failed
echo.
echo Windows packaging failed. Review the error output above.
pause
exit /b 1

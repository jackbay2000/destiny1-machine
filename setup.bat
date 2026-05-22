@echo off
title destiny1-mk Setup
echo ============================================
echo   destiny1-mk Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Download from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo [1/2] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] pip install failed. Try running this as Administrator.
    pause
    exit /b 1
)

echo.
echo [2/2] Checking ViGEmBus driver...
echo.
echo ViGEmBus is a virtual gamepad driver required by this tool.
echo If vgamepad installed successfully above, ViGEmBus was likely
echo installed automatically. If you get driver errors when running
echo destiny1-mk.py, manually install ViGEmBus from:
echo.
echo   https://github.com/ViGEm/ViGEmBus/releases/latest
echo   (download and run the ViGEmBus_Setup_x64.exe)
echo.
echo ============================================
echo   Setup complete!
echo.
echo   Next steps:
echo   1. Install chiaki-ng (see README.md)
echo   2. Run: python destiny1-mk.py
echo      (or double-click run.bat)
echo ============================================
pause

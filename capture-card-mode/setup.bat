@echo off
title destiny1-mk Capture Card Mode Setup
echo ============================================
echo   destiny1-mk Capture Card Mode Setup
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

if not exist "..\downloads" mkdir ..\downloads

:: ── Step 1: Python dependencies ──────────────────────────────────────────────
echo [1/3] Installing Python dependencies...
pip install vgamepad pynput
if errorlevel 1 (
    echo.
    echo [ERROR] pip install failed. Try running this as Administrator.
    pause
    exit /b 1
)

:: ── Step 2: ViGEmBus driver ───────────────────────────────────────────────────
echo.
echo [2/3] Downloading ViGEmBus driver (virtual controller backend)...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; $r=Invoke-RestMethod 'https://api.github.com/repos/ViGEm/ViGEmBus/releases/latest'; $a=$r.assets | Where-Object {$_.name -like '*.exe'} | Select-Object -First 1; if($a){Invoke-WebRequest -Uri $a.browser_download_url -OutFile '..\downloads\ViGEmBus_Setup_x64.exe' -UseBasicParsing}"
if not exist "..\downloads\ViGEmBus_Setup_x64.exe" (
    echo [ERROR] Failed to download ViGEmBus. Check your internet connection.
    pause
    exit /b 1
)
echo Installing ViGEmBus - complete the installer window, then come back here...
..\downloads\ViGEmBus_Setup_x64.exe
echo ViGEmBus installed.

:: ── Step 3: chiaki-ng (for controller forwarding) ─────────────────────────────
echo.
echo [3/3] Downloading chiaki-ng (needed for controller forwarding to PS4)...
echo NOTE: In capture card mode, chiaki-ng runs minimized. You won't watch its
echo       video — your game comes from the capture card in OBS instead.
echo.
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; $r=Invoke-RestMethod 'https://api.github.com/repos/streetpea/chiaki-ng/releases/latest'; $a=$r.assets | Where-Object {$_.name -match '(?i)(x64|x86_64|amd64)' -and $_.name -match '(?i)win' -and $_.name -match '\.zip$'} | Select-Object -First 1; if(-not $a){$a=$r.assets | Where-Object {$_.name -match '(?i)(x64|x86_64|amd64)' -and $_.name -match '(?i)win'} | Select-Object -First 1}; if($a){$ext=[IO.Path]::GetExtension($a.name); Invoke-WebRequest -Uri $a.browser_download_url -OutFile \"..\downloads\chiaki-ng$ext\" -UseBasicParsing} else {exit 1}"
if not exist "..\downloads\chiaki-ng.zip" if not exist "..\downloads\chiaki-ng.exe" (
    echo [ERROR] Failed to download chiaki-ng. Check your internet connection.
    pause
    exit /b 1
)
if exist "..\downloads\chiaki-ng.zip" (
    echo Extracting chiaki-ng...
    powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Expand-Archive -Path '..\downloads\chiaki-ng.zip' -DestinationPath '..\downloads\chiaki-ng-extracted' -Force"
    powershell -NoProfile -Command "if(Get-ChildItem '..\downloads\chiaki-ng-extracted\*.exe' -ErrorAction SilentlyContinue){exit 0} else {exit 1}" >nul 2>&1
    if not errorlevel 1 (
        echo Running chiaki-ng installer - complete it then come back here...
        for /f "delims=" %%f in ('dir /b "..\downloads\chiaki-ng-extracted\*.exe"') do ..\downloads\chiaki-ng-extracted\%%f
    ) else (
        if not exist "..\chiaki-ng" mkdir ..\chiaki-ng
        powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Copy-Item '..\downloads\chiaki-ng-extracted\*' -Destination '..\chiaki-ng' -Recurse -Force"
    )
) else (
    echo Running chiaki-ng installer - complete it then come back here...
    ..\downloads\chiaki-ng.exe
)

:: ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo ============================================
echo   Setup complete!
echo.
echo   Next steps:
echo   1. Enable Remote Play on your PS4 (see README-capture-card.md)
echo   2. Register your PS4 with chiaki-ng (one-time)
echo   3. Set up your capture card source in OBS
echo   4. Read README-capture-card.md for session instructions
echo ============================================
pause

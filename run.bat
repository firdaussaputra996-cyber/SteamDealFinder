@echo off
REM ============================================================
REM  run.bat - Menjalankan Steam Deal Finder Web via .venv
REM  Bisa dijalankan dengan double-click.
REM ============================================================

setlocal
cd /d "%~dp0"

set VENV_DIR=.venv

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [Setup] Membuat virtual environment di %VENV_DIR% ...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [Error] Gagal membuat virtual environment. Pastikan Python sudah terinstall dan ada di PATH.
        pause
        exit /b 1
    )

    echo [Setup] Menginstall dependensi dari requirements.txt ...
    "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
    "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [Error] Gagal menginstall dependensi.
        pause
        exit /b 1
    )
) else (
    REM Pastikan dependensi tetap terpasang/terupdate tanpa membuat ulang venv
    "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt --quiet
)

echo [Run] Menjalankan Steam Deal Finder Web ...
echo [Info] Buka http://127.0.0.1:5000 di browser.
"%VENV_DIR%\Scripts\python.exe" main.py

if errorlevel 1 (
    echo [Error] Aplikasi berhenti dengan error.
    pause
)

endlocal

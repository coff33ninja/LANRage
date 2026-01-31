@echo off
setlocal enabledelayedexpansion

echo ========================================
echo LANrage Quick Install Script
echo ========================================
echo.

REM Quick installation script for LANrage
REM Installs Chocolatey, Python 3.12, uv, and runs LANrage

echo Checking for administrator privileges...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script needs administrator privileges.
    echo Please run as administrator.
    pause
    exit /b 1
)

REM Step 1: Install Chocolatey
echo [1/5] Installing Chocolatey...
where choco >nul 2>&1 || (
    start "Chocolatey" cmd /k "powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" && pause && exit"
    echo Press any key after Chocolatey installation completes...
    pause >nul
    call refreshenv 2>nul
)

REM Step 2: Install Python 3.12
echo [2/5] Installing Python 3.12...
python --version 2>nul | findstr "3.12" >nul || (
    start "Python 3.12" cmd /k "choco install python312 -y && pause && exit"
    echo Press any key after Python installation completes...
    pause >nul
    call refreshenv 2>nul
)

REM Step 3: Upgrade pip and install uv
echo [3/5] Upgrading pip and installing uv...
start "Pip Upgrade" cmd /k "python -m pip install --upgrade pip && echo Pip upgraded! && pause && exit"
echo Press any key after pip upgrade completes...
pause >nul

where uv >nul 2>&1 || (
    start "uv Package Manager" cmd /k "echo Installing uv via PowerShell... && powershell -Command "try { irm https://astral.sh/uv/install.ps1 | iex; echo uv installed via PowerShell! } catch { echo PowerShell failed, using pip... }" && echo Installing uv via pip... && python -m pip install uv && echo uv installed! && pause && exit"
    echo Press any key after uv installation completes...
    pause >nul
)

REM Step 4: Setup environment
echo [4/5] Setting up LANrage environment...
if not exist ".venv" (
    start "LANrage Setup" cmd /k "python -m venv .venv && .venv\Scripts\activate.bat && python -m pip install --upgrade pip && python -m pip install uv && uv pip install -r requirements.txt && .venv\Scripts\python.exe setup.py && echo Setup complete! && pause && exit"
    echo Press any key after environment setup completes...
    pause >nul
)

REM Step 5: Run LANrage
echo [5/5] Starting LANrage...
start "LANrage" cmd /k ".venv\Scripts\python.exe lanrage.py"

echo.
echo LANrage is starting in a new window!
echo Web interface: http://localhost:8666
echo.
pause
exit /b 0
@echo off
setlocal enabledelayedexpansion

echo ========================================
echo LANrage Complete Installation Script
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script requires administrator privileges for Chocolatey installation.
    echo Please run as administrator.
    pause
    exit /b 1
)

echo Step 1: Installing Chocolatey (if not present)...
where choco >nul 2>&1
if %errorLevel% neq 0 (
    echo Chocolatey not found. Installing in new terminal...
    start "Installing Chocolatey" cmd /k "powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" && echo Chocolatey installation complete. Press any key to continue... && pause && exit"
    echo Waiting for Chocolatey installation to complete...
    echo Please wait for the Chocolatey installation window to finish, then press any key here.
    pause
    
    REM Refresh environment variables
    call refreshenv
) else (
    echo Chocolatey already installed.
)

echo.
echo Step 2: Installing Python 3.12 (if not present)...
python --version 2>nul | findstr "3.12" >nul
if %errorLevel% neq 0 (
    echo Python 3.12 not found. Installing in new terminal...
    start "Installing Python 3.12" cmd /k "choco install python312 -y && echo Python 3.12 installation complete. Press any key to continue... && pause && exit"
    echo Waiting for Python 3.12 installation to complete...
    echo Please wait for the Python installation window to finish, then press any key here.
    pause
    
    REM Refresh environment variables
    call refreshenv
) else (
    echo Python 3.12 already installed.
)

echo.
echo Step 3: Upgrading pip and installing uv package manager...

echo Upgrading pip in new terminal...
start "Upgrading Pip" cmd /k "echo Upgrading pip to latest version... && python -m pip install --upgrade pip && echo Pip upgraded successfully. Press any key to continue... && pause && exit"
echo Waiting for pip upgrade to complete...
echo Please wait for the pip upgrade window to finish, then press any key here.
pause

where uv >nul 2>&1
if %errorLevel% neq 0 (
    echo uv not found. Installing in new terminal...
    start "Installing uv" cmd /k "echo Installing uv package manager... && echo Method 1: PowerShell installer... && powershell -Command "try { irm https://astral.sh/uv/install.ps1 | iex; echo uv installed via PowerShell! } catch { echo PowerShell failed, trying pip... }" && echo Method 2: pip fallback... && python -m pip install uv && echo uv installation complete. Press any key to continue... && pause && exit"
    echo Waiting for uv installation to complete...
    echo Please wait for the uv installation window to finish, then press any key here.
    pause
    
    REM Refresh environment variables
    call refreshenv
) else (
    echo uv already installed.
)

echo.
echo Step 4: Setting up virtual environment and dependencies...
if not exist ".venv" (
    echo Creating virtual environment in new terminal...
    start "Setting up LANrage Environment" cmd /k "echo Creating virtual environment with Python 3.12... && python -m venv .venv && echo Virtual environment created. && echo. && echo Activating venv and upgrading pip... && .venv\Scripts\activate.bat && python -m pip install --upgrade pip && echo Pip upgraded in venv. && echo. && echo Installing uv in virtual environment... && python -m pip install uv && echo uv installed in venv. && echo. && echo Installing dependencies... && uv pip install -r requirements.txt && echo. && echo Dependencies installed successfully. && echo Press any key to continue... && pause && exit"
    echo Waiting for environment setup to complete...
    echo Please wait for the environment setup window to finish, then press any key here.
    pause
) else (
    echo Virtual environment already exists. Updating dependencies in new terminal...
    start "Updating LANrage Dependencies" cmd /k "echo Updating virtual environment... && .venv\Scripts\activate.bat && echo Upgrading pip in venv... && python -m pip install --upgrade pip && echo Upgrading uv in venv... && python -m pip install --upgrade uv && echo Updating dependencies... && uv pip install -r requirements.txt && echo Dependencies updated successfully. && echo Press any key to continue... && pause && exit"
    echo Waiting for dependency update to complete...
    echo Please wait for the dependency update window to finish, then press any key here.
    pause
)

echo.
echo Step 5: Running setup.py (if needed)...
if not exist ".env" (
    echo Running initial setup in new terminal...
    start "LANrage Initial Setup" cmd /k "echo Running LANrage setup... && .venv\Scripts\python.exe setup.py && echo Setup completed successfully. && echo Press any key to continue... && pause && exit"
    echo Waiting for setup to complete...
    echo Please wait for the setup window to finish, then press any key here.
    pause
) else (
    echo Setup already completed (.env file exists).
)

echo.
echo Step 6: Starting LANrage...
echo Starting LANrage in new terminal window...
start "LANrage - Gaming VPN" cmd /k "echo Starting LANrage... && echo. && .venv\Scripts\python.exe lanrage.py"

echo.
echo ========================================
echo Installation and startup complete!
echo ========================================
echo.
echo LANrage is now running in a separate terminal window.
echo You can access the web interface at: http://localhost:8666
echo.
echo This window can be closed safely.
echo Press any key to exit...
pause
exit /b 0
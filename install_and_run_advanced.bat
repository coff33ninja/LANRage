@echo off
setlocal enabledelayedexpansion

REM Advanced LANrage Installation Script with Error Handling
REM This version includes better error handling and fallback options

echo ========================================
echo LANrage Advanced Installation Script
echo ========================================
echo.

REM Function to check if command exists
:check_command
where %1 >nul 2>&1
exit /b %errorLevel%

REM Function to wait for user confirmation
:wait_for_user
echo Press any key when the installation window has completed...
pause >nul
goto :eof

echo Checking administrator privileges...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo WARNING: This script requires administrator privileges for some installations.
    echo Some features may not work without admin rights.
    echo.
    echo Continue anyway? (Y/N)
    set /p continue=
    if /i "!continue!" neq "Y" exit /b 1
)

echo.
echo ========================================
echo STEP 1: CHOCOLATEY INSTALLATION
echo ========================================

call :check_command choco
if %errorLevel% neq 0 (
    echo Chocolatey not found. Installing...
    echo.
    echo Opening Chocolatey installation in new window...
    start "Chocolatey Installation" cmd /c "echo Installing Chocolatey package manager... && echo. && powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; try { iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')); echo Chocolatey installed successfully! } catch { echo Failed to install Chocolatey: $_.Exception.Message }" && echo. && echo Installation window will close in 10 seconds... && timeout /t 10"
    
    call :wait_for_user
    
    REM Try to refresh environment
    if exist "%ALLUSERSPROFILE%\chocolatey\bin\RefreshEnv.cmd" (
        call "%ALLUSERSPROFILE%\chocolatey\bin\RefreshEnv.cmd"
    )
    
    REM Verify installation
    call :check_command choco
    if %errorLevel% neq 0 (
        echo WARNING: Chocolatey installation may have failed.
        echo You may need to install Python 3.12 and uv manually.
        echo Continue anyway? (Y/N)
        set /p continue=
        if /i "!continue!" neq "Y" exit /b 1
    ) else (
        echo Chocolatey installed successfully!
    )
) else (
    echo Chocolatey already installed.
)

echo.
echo ========================================
echo STEP 2: PYTHON 3.12 INSTALLATION
echo ========================================

REM Check for Python 3.12
python --version 2>nul | findstr "3.12" >nul
if %errorLevel% neq 0 (
    echo Python 3.12 not found. Checking for any Python version...
    python --version 2>nul
    if %errorLevel% neq 0 (
        echo No Python found. Installing Python 3.12...
    ) else (
        echo Found different Python version. Installing Python 3.12...
    )
    
    echo Opening Python 3.12 installation in new window...
    start "Python 3.12 Installation" cmd /c "echo Installing Python 3.12... && echo. && choco install python312 -y && echo. && echo Python 3.12 installation completed! && echo Installation window will close in 10 seconds... && timeout /t 10"
    
    call :wait_for_user
    
    REM Refresh environment
    if exist "%ALLUSERSPROFILE%\chocolatey\bin\RefreshEnv.cmd" (
        call "%ALLUSERSPROFILE%\chocolatey\bin\RefreshEnv.cmd"
    )
    
    REM Verify installation
    python --version 2>nul | findstr "3.12" >nul
    if %errorLevel% neq 0 (
        echo WARNING: Python 3.12 installation may have failed.
        echo Please install Python 3.12 manually from python.org
        echo Continue anyway? (Y/N)
        set /p continue=
        if /i "!continue!" neq "Y" exit /b 1
    ) else (
        echo Python 3.12 installed successfully!
    )
) else (
    echo Python 3.12 already installed.
)

echo.
echo ========================================
echo STEP 3: PIP UPGRADE AND UV INSTALLATION
echo ========================================

echo Upgrading pip in new window...
start "Pip Upgrade" cmd /c "echo Upgrading pip to latest version... && echo. && python -m pip install --upgrade pip && echo. && echo Pip upgraded successfully! && echo Window will close in 5 seconds... && timeout /t 5"

call :wait_for_user

call :check_command uv
if %errorLevel% neq 0 (
    echo uv not found. Installing...
    echo.
    echo Opening uv installation in new window...
    start "uv Installation" cmd /c "echo Installing uv package manager... && echo. && echo Method 1: PowerShell installer... && powershell -Command "try { irm https://astral.sh/uv/install.ps1 | iex; echo uv installed successfully via PowerShell! } catch { echo PowerShell method failed: $_.Exception.Message; echo. }" && echo. && echo Method 2: pip fallback... && python -m pip install uv && echo uv installed via pip! && echo. && echo Installation window will close in 10 seconds... && timeout /t 10"
    
    call :wait_for_user
    
    REM Refresh environment
    if exist "%ALLUSERSPROFILE%\chocolatey\bin\RefreshEnv.cmd" (
        call "%ALLUSERSPROFILE%\chocolatey\bin\RefreshEnv.cmd"
    )
    
    REM Verify installation
    call :check_command uv
    if %errorLevel% neq 0 (
        echo WARNING: uv installation may have failed via PowerShell.
        echo Trying direct pip installation...
        start "uv Pip Fallback" cmd /c "echo Installing uv via pip... && python -m pip install uv && echo uv installed successfully! && timeout /t 5"
        call :wait_for_user
        
        call :check_command uv
        if %errorLevel% neq 0 (
            echo ERROR: Could not install uv package manager.
            echo Please install manually or use pip for dependencies.
            pause
            exit /b 1
        )
    )
    echo uv installed successfully!
) else (
    echo uv already installed.
)

echo.
echo ========================================
echo STEP 4: VIRTUAL ENVIRONMENT SETUP
echo ========================================

if not exist ".venv" (
    echo Creating virtual environment...
    echo.
    echo Opening environment setup in new window...
    start "Virtual Environment Setup" cmd /c "echo Creating Python 3.12 virtual environment... && echo. && python -m venv .venv && echo Virtual environment created! && echo. && echo Activating virtual environment and upgrading pip... && .venv\Scripts\activate.bat && python -m pip install --upgrade pip && echo Pip upgraded in virtual environment! && echo. && echo Installing uv in virtual environment... && python -m pip install uv && echo uv installed in venv! && echo. && echo Installing project dependencies... && echo. && uv pip install -r requirements.txt && echo. && echo All dependencies installed successfully! && echo. && echo Setup window will close in 15 seconds... && timeout /t 15"
    
    call :wait_for_user
    
    if not exist ".venv\Scripts\python.exe" (
        echo ERROR: Virtual environment creation failed.
        echo Please check the setup window for error messages.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists. Updating dependencies...
    echo.
    echo Opening dependency update in new window...
    start "Dependency Update" cmd /c "echo Updating virtual environment... && echo. && .venv\Scripts\activate.bat && echo Upgrading pip in venv... && python -m pip install --upgrade pip && echo Installing/updating uv in venv... && python -m pip install --upgrade uv && echo Updating project dependencies... && echo. && uv pip install -r requirements.txt && echo. && echo Dependencies updated successfully! && echo. && echo Update window will close in 10 seconds... && timeout /t 10"
    
    call :wait_for_user
)

echo.
echo ========================================
echo STEP 5: LANRAGE INITIAL SETUP
echo ========================================

if not exist ".env" (
    echo Running LANrage initial setup...
    echo.
    echo Opening setup in new window...
    start "LANrage Setup" cmd /c "echo Running LANrage initial configuration... && echo. && .venv\Scripts\python.exe setup.py && echo. && echo LANrage setup completed successfully! && echo. && echo Setup window will close in 10 seconds... && timeout /t 10"
    
    call :wait_for_user
    
    if not exist ".env" (
        echo WARNING: Setup may not have completed successfully.
        echo Continue anyway? (Y/N)
        set /p continue=
        if /i "!continue!" neq "Y" exit /b 1
    )
    echo LANrage setup completed!
) else (
    echo LANrage already configured (.env file exists).
)

echo.
echo ========================================
echo STEP 6: STARTING LANRAGE
echo ========================================

echo Starting LANrage in dedicated terminal...
echo.
start "LANrage - Gaming VPN Server" cmd /k "title LANrage - Gaming VPN && echo. && echo ======================================== && echo           LANrage Gaming VPN && echo ======================================== && echo. && echo Starting LANrage server... && echo. && .venv\Scripts\python.exe lanrage.py"

echo.
echo ========================================
echo INSTALLATION COMPLETE!
echo ========================================
echo.
echo LANrage is now running in a separate terminal window.
echo.
echo Web Interface: http://localhost:8666
echo.
echo If you encounter any issues:
echo 1. Check the LANrage terminal window for error messages
echo 2. Ensure you have administrator privileges
echo 3. Check that WireGuard is installed on your system
echo 4. Review the troubleshooting guide in docs/TROUBLESHOOTING.md
echo.
echo This installation window can now be closed.
echo.
pause
exit /b 0
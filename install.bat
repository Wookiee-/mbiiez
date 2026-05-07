@echo off
REM Moviebattles II EZ Installer Tool - Windows Version
REM This script installs dependencies and configures MBIIEZ on Windows

setlocal enabledelayedexpansion

REM Get script directory
set SCRIPTPATH=%~dp0
REM Remove trailing backslash
set SCRIPTPATH=%SCRIPTPATH:~0,-1%

REM Default paths (can be customized)
set OPENJKPATH=%USERPROFILE%\nakedjk
set MBIIPATH=%OPENJKPATH%\naked
set MBIIDIR=%USERPROFILE%\.mbiiez

:menu
cls
echo *************************************************
echo       Moviebattles II EZ Installer Tool
echo            Windows Installation
echo *************************************************
echo.
echo Current paths:
echo   Script: %SCRIPTPATH%
echo   OpenJK: %OPENJKPATH%
echo   MBIIDir: %MBIIDIR%
echo.
echo Select an option:
echo.
echo   [1] Install Python Dependencies
echo   [2] Check/Install System Dependencies
echo   [3] Setup MBIIEZ Directory Structure
echo   [4] Setup RTVRTM
echo   [5] Create MBII Launcher
echo   [6] Install MBII Updater
echo   [7] Update MBII
echo   [8] Full Install (All Steps)
echo   [9] Show Current Configuration
echo  [10] Exit
echo.

set /p CHOICE=Enter your choice (1-10): 

if /i '%CHOICE%'=='1' goto :install_python
if /i '%CHOICE%'=='2' goto :install_sysdeps
if /i '%CHOICE%'=='3' goto :setup_structure
if /i '%CHOICE%'=='4' goto :setup_rtvrtm
if /i '%CHOICE%'=='5' goto :create_launcher
if /i '%CHOICE%'=='6' goto :install_updater
if /i '%CHOICE%'=='7' goto :update_mbii
if /i '%CHOICE%'=='8' goto :full_install
if /i '%CHOICE%'=='9' goto :show_config
if /i '%CHOICE%'=='10' goto :exit_menu
echo Invalid option. Please try again.
timeout /t 2 >nul
goto :menu

:install_python
cls
echo ================================================
echo Installing Python Dependencies
echo ================================================
echo.
echo This will install the following packages:
echo   - psutil     (process/system utilities)
echo   - prettytable (CLI output formatting)
echo   - six        (Python 2/3 compatibility)
echo   - watchgod   (auto-reload for development)
echo   - tailer     (log file watching)
echo   - urllib3    (HTTP library)
echo   - flask      (web framework)
echo   - flask_httpauth (API authentication)
echo   - flask-socketio (WebSocket support)
echo   - sqlite3      (VPN Monitor - built into Python 3)
echo.
echo Note: psutil is required for Windows support
echo.
set /p CONFIRM=Continue with installation? (Y/N): 
if /i not '%CONFIRM%'=='Y' goto :menu

echo.
echo Installing packages...
pip install --user psutil prettytable six watchgod tailer urllib3 flask flask_httpauth flask-socketio discord.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Python dependencies installed successfully!
) else (
    echo.
    echo [ERROR] Failed to install some packages. Check the output above.
)

echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

:install_sysdeps
cls
echo ================================================
echo Checking System Dependencies
echo ================================================
echo.

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Python is installed
    python --version
) else (
    echo [ERROR] Python not found. Please install Python 3.8+ from python.org
)

echo.

REM Check for curl
where curl >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] curl is installed
) else (
    echo [WARNING] curl not found. Some features may not work.
)

REM Check for git
where git >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] git is installed
) else (
    echo [WARNING] git not found. Some features may not work.
)

echo.
echo If any dependencies are missing, you can install them via winget:
echo   winget install cURL
echo   winget install Git.Git
echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

:setup_structure
cls
echo ================================================
echo Setting up MBIIEZ Directory Structure
echo ================================================
echo.

set /p USER_OPENJKPATH=Enter OpenJK path (default: %OPENJKPATH%): 
if not '%USER_OPENJKPATH%'=='' set OPENJKPATH=%USER_OPENJKPATH%

set /p USER_MBIIDIR=Enter MBIIDir path (default: %MBIIDIR%): 
if not '%USER_MBIIDIR%'=='' set MBIIDIR=%USER_MBIIDIR%

echo.
echo Creating directories...

REM Create MBIIDir if it doesn't exist
if not exist %MBIIDIR% (
    mkdir %MBIIDIR%
    echo [OK] Created %MBIIDIR%
) else (
    echo [OK] %MBIIDIR% already exists
)

REM Create configs directory
if not exist %MBIIDIR%\naked (
    mkdir %MBIIDIR%\naked
    echo [OK] Created %MBIIDIR%\naked
)

echo.
echo [SUCCESS] Directory structure created!
echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

:setup_rtvrtm
cls
echo ================================================
echo Setting up RTV/RTM
echo ================================================
echo.

set /p USER_OPENJKPATH=Enter OpenJK path (default: %OPENJKPATH%): 
if not '%USER_OPENJKPATH%'=='' set OPENJKPATH=%USER_OPENJKPATH%

if exist %SCRIPTPATH%\rtvrtm.py (
    copy /Y %SCRIPTPATH%\rtvrtm.py %OPENJKPATH% >nul
    echo [OK] Copied rtvrtm.py to %OPENJKPATH%
) else (
    echo [WARNING] rtvrtm.py not found in script directory
)

echo.
echo RTV/RTM setup complete. The plugin will use the config path:
echo   %OPENJKPATH%\naked\rtvrtm.json
echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

:create_launcher
cls
echo ================================================
echo Creating MBII Launcher Script
echo ================================================
echo.

set LAUNCHERPATH=%SCRIPTPATH%\nakedii.bat

REM Create the launcher batch file
(
    echo @echo off
    echo REM MBIIEZ Launcher - Auto-generated by install.bat
    echo.
    echo setlocal
    echo.
    echo REM Change to script directory
    echo cd /d %%~dp0
    echo.
    echo REM Set MBIIDir (customizable)
    echo set MBIIDIR=%%USERPROFILE%%^\.mbiiez
    echo.
    echo REM Run the Python script with any arguments passed through
    echo python %%~dp0nakedii.py %%*
    echo.
    echo endlocal
) > %LAUNCHERPATH%

if exist %LAUNCHERPATH% (
    echo [SUCCESS] Created %LAUNCHERPATH%
    echo.
    echo You can now run mbiiez using:
    echo   %LAUNCHERPATH%
    echo.
    echo Or add the script directory to your PATH for easier access.
) else (
    echo [ERROR] Failed to create launcher script.
)

echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

:install_updater
cls
echo ================================================
echo Installing MBII Updater
echo ================================================
echo.

set /p USER_OPENJKPATH=Enter OpenJK path (default: %OPENJKPATH%): 
if not '%USER_OPENJKPATH%'=='' set OPENJKPATH=%USER_OPENJKPATH%

echo.
echo This will download and install the MBII CLI Updater from moviebattles.org
echo.
set /p CONFIRM=Continue? (Y/N): 
if /i not '%CONFIRM%'=='Y' goto :menu

if exist %SCRIPTPATH%\naked (
    echo Creating update directory...
    if not exist %SCRIPTPATH%\naked mkdir %SCRIPTPATH%\naked
)

REM Download the updater (requires curl)
echo.
echo Downloading MBII CLI Updater...
curl -L -o "%SCRIPTPATH%\naked\MBII_CLI_Updater.zip" https://www.moviebattles.org/download/MBII_CLI_Updater.zip 2>nul

if %ERRORLEVEL% EQU 0 (
    echo [OK] Downloaded updater
    echo.
    echo Note: You may need to manually extract the zip file if it downloaded.
    echo       The .exe, .dll, and .json files should go to your OpenJK directory.
) else (
    echo [WARNING] Download failed. You may need to manually download from:
    echo   https://www.moviebattles.org/download/MBII_CLI_Updater.zip
)

echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

:update_mbii
cls
echo ================================================
echo Updating MBII
echo ================================================
echo.

set /p USER_OPENJKPATH=Enter OpenJK path (default: %OPENJKPATH%): 
if not '%USER_OPENJKPATH%'=='' set OPENJKPATH=%USER_OPENJKPATH%

echo.
echo This step requires .NET SDK to be installed.
echo On Windows, .NET Framework is usually pre-installed.
echo.
echo Checking for dotnet...
where dotnet >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] dotnet is installed
    dotnet --version
    echo.
    set /p CONFIRM=Run MBII Updater? (Y/N): 
    if /i '%CONFIRM%'=='Y' (
        echo.
        echo Running MBII Updater...
        cd /d %OPENJKPATH%
        dotnet MBII_CommandLine_Update_XPlatform.dll
    )
) else (
    echo [WARNING] dotnet not found. Please install from:
    echo   https://dotnet.microsoft.com/download
)

echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

:full_install
cls
echo ================================================
echo Running Full Installation
echo ================================================
echo.

echo Step 1: Installing Python dependencies...
call :install_python
echo.

echo Step 2: Checking system dependencies...
call :install_sysdeps
echo.

echo Step 3: Setting up directory structure...
call :setup_structure
echo.

echo Step 4: Setting up RTVRTM...
call :setup_rtvrtm
echo.

echo Step 5: Creating launcher...
call :create_launcher
echo.

echo ================================================
echo Full installation complete!
echo ================================================
echo.
echo Next steps:
echo   1. Copy your game server files to: %OPENJKPATH%
echo   2. Edit configs in: %MBIIDIR%\naked
echo   3. Run: %SCRIPTPATH%\nakedii.bat
echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

:show_config
cls
echo ================================================
echo Current Configuration
echo ================================================
echo.
echo Script Directory: %SCRIPTPATH%
echo OpenJK Path: %OPENJKPATH%
REM MBIIPATH not used on Windows
echo MBIIDir: %MBIIDIR%
echo.
echo Python Version:
python --version
echo.
echo Installed packages:
pip list 2>nul | findstr /I /C:psutil /C:prettytable /C:six /C:watchgod /C:tailer /C:urllib3 /C:flask /C:discord
echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

:exit_menu
echo.
echo Thank you for using MBIIEZ Installer!
echo.
exit /b 0
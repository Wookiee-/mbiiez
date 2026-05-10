@echo off
REM Moviebattles II EZ Installer Tool - Enhanced Windows Version
REM Enhanced with colors, status checks, and progress indicators

setlocal enabledelayedexpansion

REM Enable ANSI colors on Windows 10+
reg add HKCU\\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1

REM Colors (using escape sequence trick for batch)
for /f %%A in ('copy /Z /Y nul nul 2^>nul') do set BS=%%A

REM Box drawing characters
set BOX_H=-
set BOX_V=|
set BOX_TL=+
set BOX_TR=+
set BOX_BL=+
set BOX_BR=+
set BOX_RT=+
set BOX_LT=+
set BOX_TT=+
set BOX_BT=+
set BOX_CRS=+

REM Get script directory
set SCRIPTPATH=%~dp0
set SCRIPTPATH=%SCRIPTPATH:~0,-1%

REM Default paths
set OPENJKPATH=%USERPROFILE%\nakedjk
set MBIIPATH=%OPENJKPATH%\naked
set MBIIDIR=%USERPROFILE%^.mbiiez

REM ========================
REM Status Functions
REM ========================
:status_ok
echo     [OK] %~1
exit /b 0

:status_warn
echo     [WARN] %~1
exit /b 0

:status_error
echo     [ERROR] %~1
exit /b 0

:info_msg
echo     [INFO] %~1
exit /b 0

:complete_progress
echo     [DONE] %~1
exit /b 0

:print_header
echo.
echo    +---------------------------------------------------+
echo    ^|           MovieBattles II EZ Installer            ^|
echo    ^|              Enhanced Windows Menu                ^|
echo    +---------------------------------------------------+
echo.
exit /b 0

REM ========================
REM Menu
REM ========================
:menu
cls
call :print_header
echo.
echo                      Main Menu
echo    =================================================
echo.
echo    1. Install Python Dependencies
echo    2. Check System Dependencies
echo    3. Setup Directory Structure
echo    4. Setup RTVRTM
echo    5. Create MBII Launcher
echo    6. Install MBII Updater
echo    7. Update MBII
echo    8. Show Installation Status
echo    9. Quick Install (Run 1-5)
echo.
echo    0. Exit
echo.
echo    =================================================
echo.
set /p CHOICE=Enter your choice [0-9]: 

if /i '%CHOICE%'=='1' goto :install_python
if /i '%CHOICE%'=='2' goto :install_sysdeps
if /i '%CHOICE%'=='3' goto :setup_structure
if /i '%CHOICE%'=='4' goto :setup_rtvrtm
if /i '%CHOICE%'=='5' goto :create_launcher
if /i '%CHOICE%'=='6' goto :install_updater
if /i '%CHOICE%'=='7' goto :update_mbii
if /i '%CHOICE%'=='8' goto :show_status
if /i '%CHOICE%'=='9' goto :quick_install
if /i '%CHOICE%'=='0' goto :exit_menu
echo    Invalid option. Please try again.
timeout /t 2 >nul
goto :menu

REM ========================
REM Install Python Dependencies
REM ========================
:install_python
cls
echo.
echo    =================================================
echo    Installing Python Dependencies
echo    =================================================
echo.
call :info_msg Installing required Python packages...
echo.
echo    Packages: psutil, prettytable, six, watchgod, tailer,
echo             urllib3, flask, flask_httpauth, flask-socketio, discord.py
echo.
call :info_msg Running pip install...
pip install --user psutil prettytable six watchgod tailer urllib3 flask flask_httpauth flask-socketio discord.py 2>nul
if %ERRORLEVEL% EQU 0 (
    call :complete_progress Python packages installed successfully!
) else (
    call :status_error Some packages failed to install
)
echo.
echo    =================================================
echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

REM ========================
REM Check System Dependencies
REM ========================
:install_sysdeps
cls
echo.
echo    =================================================
echo    System Dependencies Check
echo    =================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :status_ok Python is installed
    python --version
) else (
    call :status_error Python not found - install from python.org
)

echo.

where curl >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :status_ok curl is installed
) else (
    call :status_warn curl not found
)

where git >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :status_ok git is installed
) else (
    call :status_warn git not found
)

where dotnet >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :status_ok dotnet is installed
) else (
    call :status_warn dotnet not found
)

echo.
call :info_msg You can install missing tools via winget:
echo    winget install Python.Python.3.12
echo    winget install cURL.cURL
echo    winget install Git.Git
echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

REM ========================
REM Setup Directory Structure
REM ========================
:setup_structure
cls
echo.
echo    =================================================
echo    Setting Up Directory Structure
echo    =================================================
echo.

set /p USER_OPENJKPATH=Enter OpenJK path (default: %OPENJKPATH%): 
if not '%USER_OPENJKPATH%'=='' set OPENJKPATH=%USER_OPENJKPATH%

set /p USER_MBIIDIR=Enter MBIIDir path (default: %MBIIDIR%): 
if not '%USER_MBIIDIR%'=='' set MBIIDIR=%USER_MBIIDIR%

echo.

call :info_msg Creating directories...
if not exist %MBIIDIR% (
    mkdir %MBIIDIR% >nul 2>&1
    call :status_ok Created %MBIIDIR%
) else (
    call :status_ok %MBIIDIR% already exists
)

if not exist %MBIIDIR%\naked (
    mkdir %MBIIDIR%\naked >nul 2>&1
    call :status_ok Created %MBIIDIR%\naked
)

echo.
call :complete_progress Directory structure ready!
echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

REM ========================
REM Setup RTVRTM
REM ========================
:setup_rtvrtm
cls
echo.
echo    =================================================
echo    Setting up RTVRTM
echo    =================================================
echo.

set /p USER_OPENJKPATH=Enter OpenJK path (default: %OPENJKPATH%): 
if not '%USER_OPENJKPATH%'=='' set OPENJKPATH=%USER_OPENJKPATH%

if exist %SCRIPTPATH%\rtvrtm.py (
    copy /Y %SCRIPTPATH%\rtvrtm.py %OPENJKPATH% >nul 2>&1
    call :status_ok Copied rtvrtm.py to OpenJK directory
) else (
    call :status_error rtvrtm.py not found in script directory
)

echo.
call :complete_progress RTVRTM setup complete!
echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

REM ========================
REM Create Launcher
REM ========================
:create_launcher
cls
echo.
echo    =================================================
echo    Creating MBII Launcher
echo    =================================================
echo.

set LAUNCHERPATH=%SCRIPTPATH%\nakedii.bat

(
    echo @echo off
    echo REM MBIIEZ Launcher - Auto-generated by install.bat
    echo setlocal
    echo cd /d %%~dp0
    echo set MBIIDIR=%%USERPROFILE%%^.mbiiez
    echo python %%~dp0nakedii.py %%*
    echo endlocal
) > %LAUNCHERPATH%

if exist %LAUNCHERPATH% (
    call :status_ok Created %LAUNCHERPATH%
    echo.
    echo    Launcher ready! Run nakedii.bat to start MBIIEZ
) else (
    call :status_error Failed to create launcher
)

echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

REM ========================
REM Install MBII Updater
REM ========================
:install_updater
cls
echo.
echo    =================================================
echo    Installing MBII Updater
echo    =================================================
echo.

set /p USER_OPENJKPATH=Enter OpenJK path (default: %OPENJKPATH%): 
if not '%USER_OPENJKPATH%'=='' set OPENJKPATH=%USER_OPENJKPATH%

if not exist %SCRIPTPATH%\naked mkdir %SCRIPTPATH%\naked

call :info_msg Downloading MBII CLI Updater...
curl -L -o "%SCRIPTPATH%\naked\MBII_CLI_Updater.zip" https://www.moviebattles.org/download/MBII_CLI_Updater.zip 2>nul

if %ERRORLEVEL% EQU 0 (
    call :complete_progress Downloaded MBII CLI Updater
    echo.
    call :info_msg Extract the zip and copy files to %OPENJKPATH%
) else (
    call :status_error Download failed - manually download from moviebattles.org
)

echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

REM ========================
REM Update MBII
REM ========================
:update_mbii
cls
echo.
echo    =================================================
echo    Updating MBII
echo    =================================================
echo.

set /p USER_OPENJKPATH=Enter OpenJK path (default: %OPENJKPATH%): 
if not '%USER_OPENJKPATH%'=='' set OPENJKPATH=%USER_OPENJKPATH%

where dotnet >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :status_error dotnet not found - please install .NET SDK first
    goto :update_mbii_done
)

call :info_msg Running MBII Command Line Updater...
cd /d %OPENJKPATH%
dotnet MBII_CommandLine_Update_XPlatform.dll 2>nul

if %ERRORLEVEL% EQU 0 (
    call :complete_progress MBII updated successfully!
) else (
    call :status_error MBII update failed
)

:update_mbii_done
echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

REM ========================
REM Show Installation Status
REM ========================
:show_status
cls
echo.
echo    =================================================
echo    Installation Status
echo    =================================================
echo.

echo    Path Information:
echo      Script: %SCRIPTPATH%
echo      OpenJK: %OPENJKPATH%
echo      MBIIDir: %MBIIDIR%
echo.

echo    Installed Components:

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :status_ok Python installed
    python --version 2>&1 | findstr /N /C:Python
) else (
    call :status_warn Python - not found
)

pip show psutil >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :status_ok Python packages installed
) else (
    call :status_warn Python packages - not installed
)

if exist %OPENJKPATH%\rtvrtm.py (
    call :status_ok RTVRTM installed
) else (
    call :status_warn RTVRTM - not installed
)

if exist %SCRIPTPATH%\nakedii.bat (
    call :status_ok Launcher created
) else (
    call :status_warn Launcher - not created
)

where dotnet >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :status_ok .NET SDK installed
) else (
    call :status_warn .NET SDK - not installed
)

echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

REM ========================
REM Quick Install
REM ========================
:quick_install
cls
echo.
echo    =================================================
echo    Running Quick Install
echo    =================================================
echo.

call :info_msg Running: Python -^> Structure -^> RTVRTM -^> Launcher
echo.
set /p CONFIRM=Press Enter to continue or Ctrl+C to cancel...

call :install_python
echo.
call :install_sysdeps
echo.
call :setup_structure
echo.
call :setup_rtvrtm
echo.
call :create_launcher

cls
echo.
echo    =================================================
echo    Quick Install Complete
echo    =================================================
echo.
call :complete_progress All core components installed!
echo.
call :info_msg Next steps:
echo    1. Copy game server files to: %OPENJKPATH%
echo    2. Edit configs in: %MBIIDIR%\naked
echo    3. Run: %SCRIPTPATH%\nakedii.bat
echo.
set /p CONTINUE=Press Enter to return to menu...
goto :menu

REM ========================
REM Exit
REM ========================
:exit_menu
echo.
echo    Thank you for using MBIIEZ Installer!
echo.
exit /b 0
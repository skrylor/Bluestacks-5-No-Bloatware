@echo off
cls
echo ==============================================
echo        BlueStacks 5 Installer Utility
echo ==============================================
echo.

:: Navigate to the directory where the batch file is located
cd /d "%~dp0"

:: Prompt the user to choose whether to run as admin
echo Do you want to run this installer with administrative privileges? [Y/N]
choice /M "Choose Y for Yes or N for No"

:: Handle the user's choice
if errorlevel 2 (
    echo.
    echo [INFO] Running the installer without administrative privileges.
    echo [WARNING] This may cause the installation to fail due to insufficient permissions.
    echo.
    goto RunScript
) else (
    echo.
    echo [INFO] Attempting to run the installer with administrative privileges...
    goto RunAsAdmin
)

:RunAsAdmin
    :: Use PowerShell to start the Python script with elevated privileges without loading profile scripts
    powershell -NoProfile -Command "Start-Process python -ArgumentList '\"bluestacks5_installer.py\"' -Verb RunAs" >nul 2>&1
    goto End

:RunScript
    :: Check if Python is installed
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not installed or not added to PATH.
        echo [INFO] Please install Python and ensure it is added to the system PATH.
        echo.
        pause
        exit /B 1
    )
    
    :: Check if the Python script exists
    if not exist "bluestacks5_installer.py" (
        echo [ERROR] Python script 'bluestacks5_installer.py' not found in the current directory.
        echo [INFO] Ensure that the Python script is located in the same directory as this batch file.
        echo.
        pause
        exit /B 1
    )

    :: Run the Python script
    echo Running the BlueStacks installer script...
    python "bluestacks5_installer.py"

    :: Check if the Python script executed successfully
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] The installer encountered an error.
    ) else (
        echo.
        echo [INFO] The installer completed successfully.
    )
    goto End

:End
    :: Pause to allow the user to read messages
    pause
    exit

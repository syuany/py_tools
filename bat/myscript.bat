@echo off
setlocal enabledelayedexpansion

:: Configure script directory (modify to your actual path)
set "SCRIPT_DIR=D:\Desktop\script"

if "%1"=="list" (
    echo Available scripts in [%SCRIPT_DIR%]:
    echo -----------------------------------
    
    for %%f in ("%SCRIPT_DIR%\*.py") do (
        echo %%~nf
    )
    
    echo -----------------------------------
    echo Usage: myscript run script_name
) else if "%1"=="run" (
    if "%2"=="" (
        echo Error: Please specify a script name
    ) else (
        if exist "%SCRIPT_DIR%\%2.py" (
            python "%SCRIPT_DIR%\%2.py"
        ) else (
            echo Error: Script '%2.py' not found
        )
    )
) else (
    echo Invalid command. Valid commands:
    echo   myscript list    List all scripts
    echo   myscript run     Execute a script
)

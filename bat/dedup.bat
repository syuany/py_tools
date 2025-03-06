@echo off
SET "script_path=%~dp0..\scripts\dedup.py"

if not exist "%script_path%" (
    echo [ERROR] Missing script: %script_path%
    pause
    exit /b 1
)

python "%script_path%" %*
if %errorlevel% neq 0 pause

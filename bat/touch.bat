@echo off
setlocal enabledelayedexpansion

:loop
if "%~1"=="" exit /b
if exist "%~1" (
    copy /b "%~1" +,, > nul 2>&1
) else (
    type nul > "%~1"
)
shift
goto loop

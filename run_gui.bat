@echo off
chcp 65001 >nul
title 16-Frame Splitter and GIF Creator
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% equ 0 (
    python main.py
    goto end
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 main.py
    goto end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" main.py
    goto end
)

echo.
echo ========================================================
echo [Error] Could not find Python in PATH or AppData.
echo ========================================================
pause

:end
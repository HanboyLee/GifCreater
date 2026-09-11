@echo off
chcp 65001 >nul
title 16-Frame Splitter and GIF Creator
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% equ 0 (
    python gif_tool.py --gui
    goto end
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 gif_tool.py --gui
    goto end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" gif_tool.py --gui
    goto end
)

echo.
echo ========================================================
echo [Error] Could not find Python in PATH or AppData.
echo ========================================================
pause

:end
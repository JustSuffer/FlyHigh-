@echo off
title FlyHigh! 3D Volleyball Launcher
echo Starting FlyHigh! 3D Volleyball Game...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Game closed with error code %errorlevel%.
    pause
)

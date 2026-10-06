@echo off
title FlyHigh! 3D Volleyball - EXE Builder
echo ========================================================
echo   FlyHigh! - 3D Volleyball Game (.EXE Builder)
echo ========================================================
echo.

echo [1/3] Checking Python dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Building standalone Windows executable with PyInstaller...
python -m PyInstaller --noconfirm --onedir --name "FlyHigh_Volleyball" --collect-all raylib --collect-all pyray main.py
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Copying assets...
if exist assets (
    xcopy /E /I /Y assets dist\FlyHigh_Volleyball\assets >nul
)

echo.
echo ========================================================
echo [SUCCESS] Build finished successfully!
echo Executable location:
echo dist\FlyHigh_Volleyball\FlyHigh_Volleyball.exe
echo ========================================================
echo.
pause

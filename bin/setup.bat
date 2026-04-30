@echo off
echo === Little Jill's Plant Nursery - Setup ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Please install Python from https://python.org/downloads
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency install failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Setting up database...
python seed_db.py
if errorlevel 1 (
    echo [ERROR] Database seed failed.
    pause
    exit /b 1
)

echo.
echo [3/3] Done!
echo.
echo -----------------------------------------------
echo  Run the app:   run.bat  (or double-click it)
echo.
echo  Test accounts:
echo    Staff:    staff@littlejillsplantnursery.com  /  staff123
echo    Customer: customer@example.com               /  password123
echo -----------------------------------------------
echo.
pause

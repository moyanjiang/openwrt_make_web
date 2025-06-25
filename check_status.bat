@echo off
echo OpenWrt Compiler - Environment Check
echo ====================================
echo.

echo Checking project structure...
if exist "backend" (echo [OK] backend directory exists) else (echo [ERROR] backend directory missing)
if exist "frontend" (echo [OK] frontend directory exists) else (echo [ERROR] frontend directory missing)
if exist "workspace" (echo [OK] workspace directory exists) else (echo [ERROR] workspace directory missing)
if exist "requirements.txt" (echo [OK] requirements.txt exists) else (echo [ERROR] requirements.txt missing)
if exist "README.md" (echo [OK] README.md exists) else (echo [ERROR] README.md missing)
echo.

echo Checking Python environment...
python --version 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Python environment is ready
) else (
    echo [ERROR] Python not installed or not in PATH
)
echo.

echo Checking virtual environment...
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment created
    venv\Scripts\python.exe test_env.py
) else (
    echo [ERROR] Virtual environment not created
    echo Please run: python -m venv venv
)
echo.

pause

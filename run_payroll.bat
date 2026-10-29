@echo off
title Payroll Pre-Export Validation & Reconciliation Engine
color 0A
cls
echo ===============================================================================
echo        PAYROLL PRE-EXPORT VALIDATION & RECONCILIATION ENGINE (YOTTAFLEX)
echo ===============================================================================
echo.
echo Starting Payroll Validation Engine...
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python main.py --scale starter
    goto end
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py main.py --scale starter
    goto end
)

echo [ERROR] Neither 'python' nor 'py' was found in your PATH.
echo Please ensure Python 3 is installed and added to your System PATH.

:end
echo.
echo ===============================================================================
echo Execution Finished. Press any key to exit this window.
echo ===============================================================================
pause >nul


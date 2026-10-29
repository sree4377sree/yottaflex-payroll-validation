@echo off
title Yottaflex Payroll Validator - Unit Tests & Reproducibility
echo =====================================================================
echo  Running Automated Test Suite & Step 10 Verification
echo =====================================================================
python -m unittest discover tests
echo.
pause

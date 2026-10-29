@echo off
title Yottaflex Payroll Validator - Enterprise Scale (3000 Employees)
echo =====================================================================
echo  Running Enterprise Scale (3,000 Employees / 190,000+ Time Entries)
echo =====================================================================
python main.py --scale full --seed 20261022
echo.
echo [DONE] Output artifacts saved in the output/ folder.
pause

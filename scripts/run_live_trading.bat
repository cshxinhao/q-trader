@echo off
setlocal EnableDelayedExpansion

:: ==================================================================================
::  SCRIPT: Tushare Checker
::  DESC:   Runs data quality checks on Tushare data
:: ==================================================================================

cd /d "%~dp0.."
set "PROJECT_ROOT=%CD%"

echo.
echo ==================================================================================
echo  [START] Live Trading
echo  Time: %DATE% %TIME%
echo  Root: %PROJECT_ROOT%
echo ==================================================================================
echo.

:: ----------------------------------------------------------------------------------
::  Environment
:: ----------------------------------------------------------------------------------
echo [INFO] Activating conda environment (tushare)...
call conda activate %PROJECT_ROOT%\venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate environment.
    exit /b %errorlevel%
)
echo.

:: ----------------------------------------------------------------------------------
::  Checks
:: ----------------------------------------------------------------------------------

echo ----------------------------------------------------------------------------------
echo [STEP] Live Trading
echo ----------------------------------------------------------------------------------
python -m examples.baseline_live_trading
echo.


echo ==================================================================================
echo  [DONE] Live Trading Completed.
echo  Time: %DATE% %TIME%
echo ==================================================================================
echo.

endlocal

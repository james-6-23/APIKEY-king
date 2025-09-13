@echo off
REM Quick launch batch script for Windows

setlocal

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\"

REM Change to project directory  
cd /d "%PROJECT_ROOT%"

REM Check if src directory exists
if not exist "src" (
    echo [ERROR] src directory not found. Are you in the correct project directory?
    exit /b 1
)

REM Parse command line argument
set "MODE=%1"

if "%MODE%"=="" (
    goto :show_help
)

REM Convert mode to lowercase (simple approach)
if /i "%MODE%"=="openrouter" set "ACTUAL_MODE=openrouter-only"
if /i "%MODE%"=="or" set "ACTUAL_MODE=openrouter-only"
if /i "%MODE%"=="modelscope" set "ACTUAL_MODE=modelscope-only"  
if /i "%MODE%"=="ms" set "ACTUAL_MODE=modelscope-only"
if /i "%MODE%"=="gemini" set "ACTUAL_MODE=gemini-only"
if /i "%MODE%"=="gm" set "ACTUAL_MODE=gemini-only"
if /i "%MODE%"=="all" set "ACTUAL_MODE=compatible"
if /i "%MODE%"=="compatible" set "ACTUAL_MODE=compatible"
if /i "%MODE%"=="help" goto :show_help
if /i "%MODE%"=="-h" goto :show_help
if /i "%MODE%"=="--help" goto :show_help

REM Check if mode was recognized
if "%ACTUAL_MODE%"=="" (
    echo [ERROR] Unknown mode: %MODE%
    echo [INFO] Run 'quick_scan.bat help' for usage information
    exit /b 1
)

REM Run the scanner
echo [INFO] Starting APIKEY-king in %ACTUAL_MODE% mode...
python -m src.main --mode "%ACTUAL_MODE%"

goto :end

:show_help
echo APIKEY-king Quick Launch Script (Windows)
echo.
echo Usage: %0 ^<mode^>
echo.
echo Available modes:
echo   openrouter, or  - Scan for OpenRouter API keys only
echo   modelscope, ms  - Scan for ModelScope API keys only  
echo   gemini, gm      - Scan for Gemini API keys only (with validation)
echo   all, compatible - Scan for all types
echo.
echo Examples:
echo   %0 openrouter   # Scan only OpenRouter keys
echo   %0 ms           # Scan only ModelScope keys
echo   %0 all          # Scan all types

:end
endlocal
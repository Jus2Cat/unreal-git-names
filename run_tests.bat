@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ============================================
echo  OFPA Test Suite
echo ============================================
echo.
echo  Tests auto-discover version folders (5_3, 5_4, ...)
echo  Performance test auto-generates and cleans up data
echo.

python -m pytest %*

if %ERRORLEVEL% equ 0 (
    echo.
    echo ============================================
    echo  All tests passed!
    echo ============================================
) else (
    echo.
    echo ============================================
    echo  Some tests failed!
    echo ============================================
)

exit /b %ERRORLEVEL%

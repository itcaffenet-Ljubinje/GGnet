@echo off
REM ============================================================================
REM GGnet Diskless System - Apply All Registry Tweaks
REM ============================================================================
REM This script applies all registry modifications for diskless Windows client
REM Run with Administrator privileges!
REM ============================================================================

echo ========================================
echo  GGnet Client Configuration
echo ========================================
echo.
echo This will apply all registry tweaks for
echo diskless operation. This requires a restart.
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Applying registry tweaks...
echo.

REM Apply each registry file
FOR %%f IN (*.reg) DO (
    IF NOT "%%f"=="apply-all.bat" (
        IF NOT "%%f"==*".template" (
            echo [*] Applying %%f...
            reg import "%%f" >nul 2>&1
            IF %ERRORLEVEL% EQU 0 (
                echo     [OK] %%f applied
            ) ELSE (
                echo     [FAIL] %%f failed
            )
        )
    )
)

echo.
echo ========================================
echo  Configuration Complete!
echo ========================================
echo.
echo Applied tweaks:
echo   - UAC disabled
echo   - Firewall disabled
echo   - RDP enabled
echo   - Performance optimized
echo   - Telemetry disabled
echo   - Client tools configured
echo.
echo IMPORTANT: A restart is required!
echo.
echo The computer will restart in 30 seconds...
echo Press Ctrl+C to cancel.
echo.

timeout /t 30

echo Restarting now...
shutdown /r /t 5 /c "GGnet: Applying diskless configuration. Please wait..."

exit /b 0


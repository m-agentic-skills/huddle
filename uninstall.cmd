@echo off
setlocal

set SKILL_NAME=huddle
set HOME_DIR=%USERPROFILE%

echo.
echo Uninstalling %SKILL_NAME%...
echo.

call :remove_from ".claude\skills" "Claude Code"
call :remove_from ".agents\skills" "Agent Skills"

echo.
echo Done.
exit /b 0

:remove_from
set REL_DIR=%~1
set LABEL=%~2
set DEST=%HOME_DIR%\%REL_DIR%\%SKILL_NAME%

if exist "%DEST%" (
  fsutil reparsepoint query "%DEST%" >nul 2>nul
  if not errorlevel 1 (
    rmdir "%DEST%"
    echo   Removed %LABEL% -^> %DEST%
  ) else (
    echo   %LABEL% -^> %DEST% is not a symlink, skipping
  )
) else (
  echo   %LABEL% -^> not installed, skipping
)
exit /b 0

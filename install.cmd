@echo off
setlocal

set SKILL_NAME=huddle
set SKILL_DIR=%~dp0
if "%SKILL_DIR:~-1%"=="\" set SKILL_DIR=%SKILL_DIR:~0,-1%

set HOME_DIR=%USERPROFILE%
set INSTALLED=0

where claude >nul 2>nul
if not errorlevel 1 (
  call :install_to ".claude\skills" "Claude Code"
  set /a INSTALLED+=1
)

where codex >nul 2>nul
if not errorlevel 1 (
  call :install_to ".agents\skills" "Agent Skills"
  set /a INSTALLED+=1
)

if %INSTALLED%==0 (
  echo No supported agent CLI detected ^(claude, codex^).
  echo Installing for Claude Code by default.
  call :install_to ".claude\skills" "Claude Code"
)

echo.
echo Done. Restart your agent session to pick up the new skill.
exit /b 0

:install_to
set REL_DIR=%~1
set LABEL=%~2
set DEST=%HOME_DIR%\%REL_DIR%\%SKILL_NAME%

if not exist "%HOME_DIR%\%REL_DIR%" mkdir "%HOME_DIR%\%REL_DIR%"

if exist "%DEST%" (
  rem Remove existing symlink or junction
  fsutil reparsepoint query "%DEST%" >nul 2>nul
  if not errorlevel 1 (
    rmdir "%DEST%"
  ) else (
    echo   %LABEL% -^> %DEST% already exists and is not a symlink, skipping
    exit /b 0
  )
)

mklink /D "%DEST%" "%SKILL_DIR%"
echo   %LABEL% -^> %DEST%
exit /b 0

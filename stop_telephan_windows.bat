@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
set "ROOT_DIR=%CD%"
set "RUN_DIR=%ROOT_DIR%\.run"

echo Arret TELEPHAN...

call :stop_pid_file Backend "%RUN_DIR%\backend.pid"
call :stop_pid_file Frontend "%RUN_DIR%\frontend.pid"

where docker >nul 2>&1
if not errorlevel 1 (
  docker compose -f "%ROOT_DIR%\docker-compose.yml" stop mariadb phpmyadmin >nul 2>&1
  echo - Docker: mariadb + phpMyAdmin stoppes
)

echo OK
exit /b 0

:stop_pid_file
set "LABEL=%~1"
set "PID_FILE=%~2"
if not exist "%PID_FILE%" (
  echo - %LABEL%: aucun PID
  exit /b 0
)

set "PID="
set /p PID=<"%PID_FILE%"
if "%PID%"=="" (
  echo - %LABEL%: aucun PID
  del /q "%PID_FILE%" >nul 2>&1
  exit /b 0
)

tasklist /FI "PID eq %PID%" | find "%PID%" >nul 2>&1
if errorlevel 1 (
  echo - %LABEL%: deja arrete
) else (
  taskkill /PID %PID% /T /F >nul 2>&1
  if errorlevel 1 (
    echo - %LABEL%: echec arret ^(PID %PID%^)
  ) else (
    echo - %LABEL%: arret ^(PID %PID%^)
  )
)

del /q "%PID_FILE%" >nul 2>&1
exit /b 0

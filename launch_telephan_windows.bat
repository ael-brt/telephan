@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
set "ROOT_DIR=%CD%"
set "RUN_DIR=%ROOT_DIR%\.run"
set "BACKEND_DIR=%ROOT_DIR%\qlio_dash"
set "FRONTEND_DIR=%ROOT_DIR%\visual-identical-twin-main"
set "BACKEND_LOG=%RUN_DIR%\backend.log"
set "FRONTEND_LOG=%RUN_DIR%\frontend.log"
set "BACKEND_PID_FILE=%RUN_DIR%\backend.pid"
set "FRONTEND_PID_FILE=%RUN_DIR%\frontend.pid"

if not exist "%RUN_DIR%" mkdir "%RUN_DIR%"

if not exist "%ROOT_DIR%\.env" if exist "%ROOT_DIR%\.env.example" (
  copy /Y "%ROOT_DIR%\.env.example" "%ROOT_DIR%\.env" >nul
  echo [INFO] .env cree depuis .env.example
)

if exist "%ROOT_DIR%\.env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%ROOT_DIR%\.env") do (
    if not "%%~A"=="" set "%%~A=%%~B"
  )
)

where docker >nul 2>&1
if errorlevel 1 (
  echo [ERREUR] Docker introuvable dans le PATH.
  exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
  where py >nul 2>&1
  if errorlevel 1 (
    echo [ERREUR] Python introuvable dans le PATH.
    exit /b 1
  )
)

where npm >nul 2>&1
if errorlevel 1 (
  echo [ERREUR] npm introuvable dans le PATH.
  exit /b 1
)

echo [1/5] Demarrage MariaDB...
docker compose up -d mariadb >nul
if errorlevel 1 (
  echo [ERREUR] Echec demarrage MariaDB. Verifier Docker Desktop.
  exit /b 1
)

docker compose up -d phpmyadmin >nul 2>&1
if errorlevel 1 (
  echo [INFO] phpMyAdmin non lance ^(optionnel^).
)

echo [2/5] Verification backend Python...
if not exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
  echo   - Creation du venv backend...
  where py >nul 2>&1
  if errorlevel 1 (
    python -m venv "%BACKEND_DIR%\.venv"
  ) else (
    py -3 -m venv "%BACKEND_DIR%\.venv"
  )
  if errorlevel 1 (
    echo [ERREUR] Impossible de creer le venv backend.
    exit /b 1
  )
)

"%BACKEND_DIR%\.venv\Scripts\python.exe" -c "import django, pandas, MySQLdb" >nul 2>&1
if errorlevel 1 (
  echo   - Installation des dependances backend ^(premier lancement^)...
  "%BACKEND_DIR%\.venv\Scripts\pip.exe" install -r "%BACKEND_DIR%\requirements.txt"
  if errorlevel 1 (
    echo [ERREUR] Installation des dependances backend en echec.
    exit /b 1
  )
)

echo [3/5] Verification frontend Node...
if not exist "%FRONTEND_DIR%\node_modules" (
  echo   - Installation des dependances frontend ^(premier lancement^)...
  pushd "%FRONTEND_DIR%" >nul
  npm install
  set "NPM_RC=!ERRORLEVEL!"
  popd >nul
  if not "!NPM_RC!"=="0" (
    echo [ERREUR] Installation des dependances frontend en echec.
    exit /b 1
  )
)

echo [4/5] Lancement backend Django...
call :process_running "%BACKEND_PID_FILE%"
if "%ERRORLEVEL%"=="0" (
  set /p BPID=<"%BACKEND_PID_FILE%"
  echo   - Backend deja en cours ^(PID !BPID!^)
) else (
  if not defined USE_SQLITE_FALLBACK set "USE_SQLITE_FALLBACK=0"
  set "DB_HOST=127.0.0.1"
  set "DB_PORT=3306"
  if not defined FRONTEND_BASE_URL set "FRONTEND_BASE_URL=http://127.0.0.1:8080"
  set "ENERGY_CSV_PATH=%ROOT_DIR%\dataEnergy.csv"

  "%BACKEND_DIR%\.venv\Scripts\python.exe" "%BACKEND_DIR%\manage.py" migrate >>"%BACKEND_LOG%" 2>&1
  if errorlevel 1 (
    echo [ERREUR] Echec migration backend. Voir: %BACKEND_LOG%
    exit /b 1
  )

  powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process -FilePath '%BACKEND_DIR%\\.venv\\Scripts\\python.exe' -ArgumentList 'manage.py','runserver','127.0.0.1:8000','--noreload' -WorkingDirectory '%BACKEND_DIR%' -RedirectStandardOutput '%BACKEND_LOG%' -RedirectStandardError '%BACKEND_LOG%' -PassThru; $p.Id | Out-File -Encoding ascii '%BACKEND_PID_FILE%'"

  timeout /t 2 /nobreak >nul
  call :process_running "%BACKEND_PID_FILE%"
  if not "%ERRORLEVEL%"=="0" (
    echo [ERREUR] Echec lancement backend. Voir: %BACKEND_LOG%
    exit /b 1
  )
  set /p BPID=<"%BACKEND_PID_FILE%"
  echo   - Backend lance ^(PID !BPID!^)
)

echo [5/5] Lancement frontend Vite...
call :process_running "%FRONTEND_PID_FILE%"
if "%ERRORLEVEL%"=="0" (
  set /p FPID=<"%FRONTEND_PID_FILE%"
  echo   - Frontend deja en cours ^(PID !FPID!^)
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process -FilePath 'npm.cmd' -ArgumentList 'run','dev','--','--host','127.0.0.1','--port','8080','--strictPort' -WorkingDirectory '%FRONTEND_DIR%' -RedirectStandardOutput '%FRONTEND_LOG%' -RedirectStandardError '%FRONTEND_LOG%' -PassThru; $p.Id | Out-File -Encoding ascii '%FRONTEND_PID_FILE%'"

  timeout /t 2 /nobreak >nul
  call :process_running "%FRONTEND_PID_FILE%"
  if not "%ERRORLEVEL%"=="0" (
    echo [ERREUR] Echec lancement frontend. Voir: %FRONTEND_LOG%
    exit /b 1
  )
  set /p FPID=<"%FRONTEND_PID_FILE%"
  echo   - Frontend lance ^(PID !FPID!^)
)

echo.
echo TELEPHAN Dashboard:
echo - Frontend   : http://127.0.0.1:8080
echo - Backend    : http://127.0.0.1:8000
echo - phpMyAdmin : http://127.0.0.1:8081 ^(optionnel^)
echo.
echo Logs:
echo - %BACKEND_LOG%
echo - %FRONTEND_LOG%
echo.
echo Pour arreter: stop_telephan_windows.bat

start "" "http://127.0.0.1:8080" >nul 2>&1
exit /b 0

:process_running
set "PID_FILE=%~1"
if not exist "%PID_FILE%" exit /b 1
set "PID="
set /p PID=<"%PID_FILE%"
if "%PID%"=="" exit /b 1
for /f "tokens=2 delims=," %%P in ('tasklist /FI "PID eq %PID%" /FO CSV /NH 2^>nul') do (
  if "%%~P"=="%PID%" exit /b 0
)
exit /b 1

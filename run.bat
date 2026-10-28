@echo off
rem ===========================================================================
rem  Learnora - one-click local run (Windows)
rem  Sets up anything that is missing, then starts the API and the website.
rem ===========================================================================
setlocal EnableExtensions
cd /d "%~dp0"

title SkillEarn launcher
echo ============================================================
echo   SkillEarn - starting up
echo ============================================================
echo.

rem ---- Check the tools we need -------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
  echo [X] Python was not found on your PATH.
  echo     Install Python 3.11 or newer from https://www.python.org/downloads/
  echo     and tick "Add python.exe to PATH" during setup.
  goto :fail
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [X] npm was not found on your PATH.
  echo     Install Node.js 20 or newer from https://nodejs.org/ and try again.
  goto :fail
)

set "VENV_PY=%~dp0backend\.venv\Scripts\python.exe"
set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"

rem ---- 1. Python virtual environment -------------------------------------
if exist "%VENV_PY%" (
  echo [1/5] Python virtual environment already exists.
) else (
  echo [1/5] Creating the Python virtual environment...
  python -m venv "%BACKEND_DIR%\.venv"
  if errorlevel 1 goto :fail
)

rem ---- 2. Backend dependencies ------------------------------------------
echo [2/5] Installing backend dependencies...
"%VENV_PY%" -m pip install --upgrade pip --quiet
"%VENV_PY%" -m pip install -r "%BACKEND_DIR%\requirements.txt" --quiet
if errorlevel 1 (
  echo [X] Could not install the backend dependencies.
  goto :fail
)

rem ---- 3. backend\.env --------------------------------------------------
if exist "%BACKEND_DIR%\.env" (
  echo [3/5] backend\.env already exists.
) else (
  echo [3/5] Creating backend\.env with a fresh JWT secret...
  powershell -NoProfile -Command "$secret = & '%VENV_PY%' -c 'import secrets; print(secrets.token_urlsafe(48))'; (Get-Content '%BACKEND_DIR%\.env.example' -Raw) -replace 'change-me-in-production-please-use-a-long-random-value', $secret | Set-Content -Path '%BACKEND_DIR%\.env' -Encoding utf8"
  if errorlevel 1 goto :fail
  echo.
  echo [!] Set DATABASE_URL in backend\.env to your PostgreSQL database before
  echo     the API can start. Every write is stored there - there is no local
  echo     file database fallback.
  echo.
)

rem ---- 4. Database ------------------------------------------------------
echo [4/5] Applying migrations and adding the sample catalogue...
pushd "%BACKEND_DIR%"
"%VENV_PY%" -m alembic upgrade head
if errorlevel 1 (
  popd
  echo [X] The database migrations failed. Read the message above.
  goto :fail
)
"%VENV_PY%" scripts\seed.py
if errorlevel 1 echo [!] Seeding failed, but the app can still start. Read the message above.
popd

rem ---- 5. Frontend dependencies -----------------------------------------
if exist "%FRONTEND_DIR%\node_modules" (
  echo [5/5] Frontend dependencies already installed.
) else (
  echo [5/5] Installing frontend dependencies ^(this takes a minute^)...
  pushd "%FRONTEND_DIR%"
  call npm install --no-fund --no-audit
  if errorlevel 1 (
    popd
    echo [X] npm install failed. Read the message above.
    goto :fail
  )
  popd
)

rem ---- Start both servers in their own windows --------------------------
echo.
echo Starting the servers...

set "API_RUNNING="
set "WEB_RUNNING="
netstat -ano | findstr /C:":8000 " | findstr /I /C:"LISTENING" >nul 2>nul
if not errorlevel 1 set "API_RUNNING=1"
netstat -ano | findstr /C:":5173 " | findstr /I /C:"LISTENING" >nul 2>nul
if not errorlevel 1 set "WEB_RUNNING=1"

if defined API_RUNNING (
  echo [!] Port 8000 is already taken, so the API is probably running already.
  echo     Skipping the API window - close the other one first to restart it.
) else (
  start "Learnora API" /D "%BACKEND_DIR%" cmd /k ""%VENV_PY%" -m uvicorn app.main:app --reload --port 8000"
)

if defined WEB_RUNNING (
  echo [!] Port 5173 is already taken, so the website is probably running already.
  echo     Skipping the website window - close the other one first to restart it.
) else (
  start "Learnora Web" /D "%FRONTEND_DIR%" cmd /k "npm run dev"
)

echo.
echo ============================================================
echo   Learnora is running
echo ============================================================
echo   API docs : http://127.0.0.1:8000/docs
echo   Website  : http://localhost:5173
echo.
echo   Admin login : admin@skillearn.dev / Admin@12345
echo.
echo   The API and the website each run in their own window.
echo   Close them (or press Ctrl+C in them) to stop.
echo ============================================================
echo.

echo Waiting for the servers to wake up...
timeout /t 6 /nobreak >nul
start "" "http://localhost:5173"

echo Done. You can close this window.
timeout /t 5 /nobreak >nul
exit /b 0

:fail
echo.
echo Setup stopped. Fix the problem above and run this file again.
echo.
pause
exit /b 1

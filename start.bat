@echo off
REM Circle - one-click start. Uses port 8008 because 8000 is often taken by other projects.
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv venv
  venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo Applying database migrations...
venv\Scripts\python.exe manage.py migrate --noinput

echo.
echo Circle is starting at http://127.0.0.1:8008/login/
echo Press Ctrl+C to stop the server.
echo.
venv\Scripts\python.exe manage.py runserver 8008
pause

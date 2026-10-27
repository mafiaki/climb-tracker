@echo off
cd /d "%~dp0"
where python >nul 2>nul || (
  echo No se encontro Python. Instala Python 3 desde https://www.python.org y marca "Add to PATH".
  pause
  exit /b 1
)
python -c "import webview, curl_cffi" >nul 2>nul || (
  echo Instalando lo necesario, solo pasa la primera vez...
  python -m pip install -r requirements.txt || (
    pause
    exit /b 1
  )
)
start "" pythonw "Climb Tracker.pyw"

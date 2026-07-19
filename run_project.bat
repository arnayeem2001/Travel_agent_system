@echo off
if not exist ".venv\Scripts\python.exe" (
    echo .venv was not found.
    echo Run: py -3.11 -m venv .venv
    echo Then: .venv\Scripts\activate
    echo Then: python -m pip install -r requirements.txt
    pause
    exit /b 1
)

start "Travel Agent Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn fastapi_travel_agent:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 3 /nobreak >nul
start "Travel Agent Frontend" cmd /k ".venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8501"

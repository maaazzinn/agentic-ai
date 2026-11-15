@echo off
cd /d "%~dp0"
echo Starting FastAPI Ollama Server...
call .venv\Scripts\activate
python run.py
pause

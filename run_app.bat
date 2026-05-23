@echo off
chcp 65001 >nul
title Multimodal ReAct Agent
cd /d "D:\Multimodal Project\multimodal_agent"
set PYTHONIOENCODING=utf-8
echo ============================================
echo    Multimodal ReAct Agent
echo    http://127.0.0.1:7860
echo ============================================
echo.
echo Checking port 7860...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":7860.*LISTENING"') do (
    echo Killing old process PID %%a
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)
echo.
echo Starting server...
echo Press Ctrl+C to stop.
echo.
"D:\Qwen 2.5 7B\env\python.exe" -X utf8 app.py
pause

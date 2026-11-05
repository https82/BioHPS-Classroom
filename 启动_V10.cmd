@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "..\BioHPS_V6_2\.venv\Scripts\python.exe" set "PYTHON_EXE=..\BioHPS_V6_2\.venv\Scripts\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=python"
"%PYTHON_EXE%" -m streamlit --version >nul 2>&1
if errorlevel 1 (
  echo [BioHPS] Python环境中没有找到Streamlit。
  echo 请在项目文件夹的PowerShell中执行：
  echo python -m pip install -r requirements.txt
  pause
  exit /b 1
)
"%PYTHON_EXE%" -m streamlit run app.py
pause

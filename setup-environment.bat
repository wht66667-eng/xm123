@echo off
cd /d "%~dp0"
python --version
if errorlevel 1 goto missing
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 goto failed
python -m pip install -r mobile\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 goto failed
python configure.py
pause
exit /b 0
:missing
echo Install Python 3.11 and add Python to PATH first.
pause
exit /b 1
:failed
echo Dependency installation failed. Check network and retry.
pause
exit /b 1

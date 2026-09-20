@echo off
setlocal
cd /d "%~dp0"
if defined PYTHON (
  "%PYTHON%" -B src_zx\build.py
) else (
  python -B src_zx\build.py
)
exit /b %errorlevel%

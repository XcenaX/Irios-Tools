@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo Rebuilding Irios Tools desktop app
echo Project: %CD%
echo ========================================
echo.

if not exist ".tmp" mkdir ".tmp"

set "ROOT=%CD%"
set "ENTRY=%ROOT%\.tmp\irios_desktop_entry.py"
set "DIST=%ROOT%\.tmp\package_onefile"
set "BUILD=%ROOT%\.tmp\package_build_onefile"
set "OLD_ONEDIR=%ROOT%\.tmp\package_dist\Irios Tools"
set "EXE=%DIST%\Irios Tools.exe"

if exist "%OLD_ONEDIR%" rmdir /s /q "%OLD_ONEDIR%"
if exist "%EXE%" del /f /q "%EXE%"

> "%ENTRY%" (
    echo from desktop_app.app.main import run
    echo.
    echo.
    echo if __name__ == "__main__":
    echo     run^(^)
)

python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onefile ^
  --name "Irios Tools" ^
  --icon "%ROOT%\assets\icon.ico" ^
  --distpath "%DIST%" ^
  --workpath "%BUILD%" ^
  --specpath "%ROOT%\.tmp" ^
  --add-data "%ROOT%\assets;assets" ^
  --add-data "%ROOT%\data;data" ^
  --add-data "%ROOT%\templates;templates" ^
  --add-data "%ROOT%\shared;shared" ^
  --add-data "%ROOT%\desktop_app;desktop_app" ^
  --hidden-import desktop_app.modules.hr_documents.page ^
  --hidden-import desktop_app.modules.materials_writeoff.page ^
  --hidden-import pymorphy3_dicts_ru ^
  --collect-data pymorphy3_dicts_ru ^
  "%ENTRY%"

if errorlevel 1 (
    echo.
    echo ========================================
    echo Build failed. See errors above.
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build finished successfully.
echo Open this file:
echo %EXE%
echo ========================================
echo.
pause

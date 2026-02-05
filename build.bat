@echo off
echo Building Certificate Generator...
echo.

REM Install PyInstaller if not already installed
pip install pyinstaller

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist launch.spec del launch.spec

REM Build the executable
pyinstaller --onefile --name "CertificateGenerator" --icon=NONE launch.py

echo.
echo Build complete!
echo.
echo The executable is in the 'dist' folder.
echo To distribute, copy the entire project folder including:
echo   - dist/CertificateGenerator.exe
echo   - app.py
echo   - requirements.txt
echo   - Any template files
echo.
pause

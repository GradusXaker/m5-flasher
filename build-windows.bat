@echo off
setlocal

if not exist .venv (
  py -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -e .
pip install pyinstaller
pyinstaller --noconfirm --windowed --name GradusFlasher src\m5_flasher\main.py

echo.
echo Windows build complete.
echo Output: dist\GradusFlasher\GradusFlasher.exe

endlocal

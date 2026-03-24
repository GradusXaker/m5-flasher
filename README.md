# M5 Flasher

Desktop app for flashing `M5Stick` devices over a serial port.

## Features

- Detect available serial ports
- Choose a firmware `.bin` file
- Download latest Bruce firmware for supported M5Stick profiles
- Flash with `esptool`
- Show live logs and progress
- Hacker-style black and green UI
- Save last used profile, port, baud, offset, and firmware path

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m m5_flasher.main
```

## Build

```bash
source .venv/bin/activate
pip install pyinstaller
pyinstaller --noconfirm --windowed --name M5Flasher src/m5_flasher/main.py
```

Built app output:

- Linux: `dist/M5Flasher/M5Flasher`

## Notes

- Default flash offset is `0x0`
- The app is optimized for `M5Stick` and similar ESP32-based devices
- Some boards may need manual boot/download mode before flashing
- Latest Bruce profile options currently include `M5Stick S3`, `M5StickC Plus2`, and `M5StickC Plus 1.1`

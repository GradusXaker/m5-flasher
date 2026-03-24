# Сборка Gradus Flasher в `.exe` на Windows

Из текущего Linux-окружения я не могу честно собрать и проверить нативный `Windows .exe`, поэтому подготовлен готовый сценарий сборки для Windows.

Кроме локальной сборки, в репозитории настроен workflow `.github/workflows/windows-release.yml`, который собирает Windows-версию автоматически по тегу `v*`.

## Что нужно

- `Windows 10/11`
- `Python 3.11+`
- `Git`

## Быстрый способ

Открой `PowerShell` или `cmd` в папке проекта и запусти:

```powershell
build-windows.bat
```

## Что делает скрипт

- создает `.venv`, если его еще нет;
- активирует окружение;
- обновляет `pip`;
- ставит зависимости проекта;
- ставит `pyinstaller`;
- собирает `GradusFlasher.exe`.

## Где будет результат

```text
dist\GradusFlasher\GradusFlasher.exe
```

## Ручная сборка без bat-файла

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
pip install pyinstaller
pyinstaller --noconfirm --windowed --name GradusFlasher src\m5_flasher\main.py
```

## Что проверить после сборки

1. Запускается ли `dist\GradusFlasher\GradusFlasher.exe`
2. Видит ли приложение `COM`-порт
3. Открываются ли `INSTALL.md` и `WINDOWS_INSTALL.md`
4. Работают ли кнопки `Проверить устройство`, `Анализ .bin` и `ПРОШИТЬ УСТРОЙСТВО`

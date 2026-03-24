# Установка Gradus Flasher

Подробная инструкция по установке, запуску и первой прошивке.

## Что это за проект

`Gradus Flasher` — desktop-приложение для прошивки устройств `M5Stick` и других совместимых `ESP32`-плат через serial-порт.

Сейчас проект сделан на `Python + PySide6`.

Почему так:

- быстрее развивать и проверять рабочий MVP;
- удобно работать с `esptool` и serial-портами;
- проще собирать desktop-приложение;
- текущая версия уже реализована и проверена.

Если позже захочешь, проект можно переписать на `C` или `JavaScript`, но для текущего прошивальщика это не обязательно.

## Что нужно перед установкой

### Windows

Установи:

- `Python 3.11+` или новее;
- `Git`;
- при необходимости драйвер для USB-UART устройства (`CH340`, `CP210x` или другой, который использует твоя плата).

Проверь команды:

```powershell
python --version
pip --version
git --version
```

Если `python` не найден, попробуй:

```powershell
py --version
```

### Linux

Нужно:

- `Python 3.11+`;
- `pip`;
- `git`;
- доступ к serial-порту.

Проверка:

```bash
python3 --version
pip3 --version
git --version
```

Если нет доступа к порту, часто помогает:

```bash
sudo usermod -aG dialout $USER
```

После этого обычно нужно перелогиниться.

## 1. Скачать проект

Если репозиторий уже есть у тебя локально, этот шаг можно пропустить.

```bash
git clone git@github.com:GradusXaker/m5-flasher.git
cd m5-flasher
```

Или через HTTPS:

```bash
git clone https://github.com/GradusXaker/m5-flasher.git
cd m5-flasher
```

## 2. Создать виртуальное окружение

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Если используешь `py`:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

После активации в начале строки обычно появится `(.venv)`.

## 3. Установить зависимости

### Linux / macOS

```bash
pip install --upgrade pip
pip install -e .
```

### Windows PowerShell

```powershell
python -m pip install --upgrade pip
pip install -e .
```

Эта команда установит:

- `PySide6` — графический интерфейс;
- `pyserial` — работа с serial/COM-портами;
- `esptool` — прошивка `ESP32`.

## 4. Запустить приложение

### Универсальный способ

```bash
python -m m5_flasher.main
```

### Через console script

```bash
m5-flasher
```

Если запускаешь на Windows и команда `m5-flasher` не найдена, используй первый вариант через `python -m`.

## 5. Как прошить устройство

1. Подключи `M5Stick` по USB.
2. Открой `Gradus Flasher`.
3. Нажми `Обновить порты`.
4. Выбери нужный `serial`/`COM`-порт.
5. Выбери профиль `Gradus` или свой `.bin` файл.
6. Если хочешь скачать совместимую прошивку автоматически, нажми `Скачать последний Gradus`.
7. Убедись, что `offset` равен `0x0`, если у тебя обычный single-image `.bin`.
8. При необходимости переведи плату в boot/download mode.
9. Нажми `ПРОШИТЬ УСТРОЙСТВО`.
10. Следи за логом и прогресс-баром.

## 6. Как перевести M5Stick в режим прошивки

Для `M5Stick` часто нужен ручной вход в boot mode.

Типовой сценарий:

1. Выключи устройство.
2. Замкни `G0 -> GND`.
3. Подключи USB.
4. Убери перемычку.
5. Запусти прошивку из приложения.

Если плата не определяется:

- переподключи кабель;
- попробуй другой USB-кабель;
- проверь драйвер;
- снова обнови список портов.

## 7. Сборка standalone-приложения

Если хочешь собрать отдельный desktop-бинарник:

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name GradusFlasher src/m5_flasher/main.py
```

Результат сборки:

- Linux: `dist/GradusFlasher/GradusFlasher`

## 8. Частые проблемы

### Не видно COM/serial-порт

- нажми `Обновить порты`;
- проверь USB-кабель;
- установи драйвер;
- закрой программы, которые могли занять порт.

### Ошибка доступа к порту

На Linux проверь права к устройству `/dev/ttyUSB*` или `/dev/ttyACM*`.

На Windows проверь, не занят ли `COM` другой программой.

### Прошивка не стартует

- проверь, что выбран правильный `.bin`;
- проверь `offset`, обычно это `0x0`;
- переведи плату в boot mode вручную;
- попробуй включить `Стереть flash перед записью`.

### Окно запускается, но ничего не происходит

Запусти из терминала:

```bash
python -m m5_flasher.main
```

Тогда ошибки будет проще увидеть прямо в консоли.

## 9. Что важно знать про Gradus

- интерфейс и брендинг в приложении называются `Gradus`;
- для совместимости загрузка может использовать upstream-релизы с именами файлов вида `Bruce-...`;
- локально скачанный файл приложение переименовывает в `Gradus-...`, если это возможно.

## 10. Рекомендуемый сценарий установки

Если хочешь просто начать без лишней возни, делай так:

```bash
git clone git@github.com:GradusXaker/m5-flasher.git
cd m5-flasher
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
python -m m5_flasher.main
```

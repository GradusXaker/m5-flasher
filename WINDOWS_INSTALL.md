# Установка Gradus Flasher на Windows

Отдельная инструкция для `Windows 10/11`.

## 1. Что установить заранее

Тебе понадобятся:

- `Python 3.11` или новее;
- `Git for Windows`;
- драйвер USB-UART, если плата не определяется автоматически.

Чаще всего для `M5Stick` и похожих устройств нужны драйверы под:

- `CH340`;
- `CP210x`.

## 2. Проверка Python

Открой `PowerShell` и выполни:

```powershell
python --version
```

Если не работает, попробуй:

```powershell
py --version
```

Если Python вообще не установлен, поставь его с официального сайта и во время установки включи опцию добавления в `PATH`.

## 3. Клонирование проекта

Открой `PowerShell` и выполни:

```powershell
git clone https://github.com/GradusXaker/m5-flasher.git
cd m5-flasher
```

## 4. Создание виртуального окружения

Если работает `python`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Если работает только `py`:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

После активации ты увидишь `(.venv)` слева в строке терминала.

## 5. Установка зависимостей

```powershell
python -m pip install --upgrade pip
pip install -e .
```

## 6. Запуск приложения

```powershell
python -m m5_flasher.main
```

Если все в порядке, откроется окно `Gradus Flasher`.

## 7. Как прошить устройство

1. Подключи устройство по USB.
2. Если Windows просит драйвер, установи его.
3. Запусти `Gradus Flasher`.
4. Нажми `Обновить порты`.
5. Выбери нужный `COM`-порт.
6. Выбери `.bin` файл или профиль `Gradus`.
7. При необходимости нажми `Скачать последний Gradus`.
8. Нажми `Проверить устройство`, чтобы проверить связь, определить чип и получить подсказку по профилю.
9. Нажми `ПРОШИТЬ УСТРОЙСТВО`.

## 8. Если COM-порт не появляется

- попробуй другой USB-кабель;
- переподключи устройство;
- открой `Диспетчер устройств` и проверь, появился ли новый `COM`;
- установи драйвер `CH340` или `CP210x`;
- закрой программы, которые могли занять порт.

## 9. Если PowerShell блокирует активацию venv

Иногда Windows не дает выполнить `Activate.ps1`.

Тогда в `PowerShell` можно временно разрешить скрипты для текущего пользователя:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

После этого снова выполни:

```powershell
.venv\Scripts\Activate.ps1
```

## 10. Сборка desktop-билда

Если хочешь собрать отдельный `.exe`-проект позже:

```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --name GradusFlasher src/m5_flasher/main.py
```

## 11. Самый короткий путь

Если хочешь минимум действий:

```powershell
git clone https://github.com/GradusXaker/m5-flasher.git
cd m5-flasher
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
python -m m5_flasher.main
```

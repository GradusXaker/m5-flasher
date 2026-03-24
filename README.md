# Gradus Flasher

Desktop-приложение для прошивки устройств `M5Stick` через serial-порт.

## Возможности

- Поиск доступных serial-портов
- Выбор файла прошивки `.bin`
- Загрузка последней прошивки `Gradus` для поддерживаемых профилей `M5Stick`
- Прошивка через `esptool`
- Живой лог и прогресс выполнения
- Хакерский черно-зеленый интерфейс
- Сохранение последнего профиля, порта, baud, offset и пути к файлу

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m m5_flasher.main
```

## Сборка

```bash
source .venv/bin/activate
pip install pyinstaller
pyinstaller --noconfirm --windowed --name GradusFlasher src/m5_flasher/main.py
```

Готовый билд после сборки:

- Linux: `dist/GradusFlasher/GradusFlasher`

## Заметки

- Стандартный flash offset: `0x0`
- Приложение оптимизировано под `M5Stick` и похожие устройства на `ESP32`
- Некоторым платам может понадобиться ручной вход в boot/download mode перед прошивкой
- Сейчас доступны профили `Gradus` для `M5Stick S3`, `M5StickC Plus2` и `M5StickC Plus 1.1`
- Под капотом загрузка использует совместимые upstream-бинарники, поэтому реальные имена исходных release-артефактов могут начинаться с `Bruce-`

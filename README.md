# Gradus Flasher

![Gradus Flasher Banner](docs/banner.svg)

Desktop-приложение для прошивки устройств `M5Stick` через serial-порт.

Подробная инструкция по установке и запуску: `INSTALL.md`

Отдельная инструкция для Windows: `WINDOWS_INSTALL.md`

Сборка `.exe` под Windows: `BUILD_WINDOWS.md`

История изменений: `CHANGELOG.md`

## Возможности

- Поиск доступных serial-портов
- Выбор файла прошивки `.bin`
- Загрузка последней прошивки `Gradus` для поддерживаемых профилей `M5Stick`
- Прошивка через `esptool`
- Пошаговый мастер прошивки для первого запуска
- Проверка подключения, автоопределение чипа и подсказка профиля до прошивки
- Анализ `.bin`, встроенный центр релизов и проверка обновлений
- Живой лог и прогресс выполнения
- Хакерский черно-зеленый интерфейс
- История операций и сохранение последних настроек
- Страница `О программе` и встроенные ссылки на релизы/репозиторий

## Скриншоты

### Главное окно

![Главное окно Gradus Flasher](docs/screenshots/main-window.png)

### Мастер прошивки

![Мастер прошивки Gradus](docs/screenshots/wizard-window.png)

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

Автоматическая Windows-сборка настроена через GitHub Actions: `.github/workflows/windows-release.yml`

Готовый билд после сборки:

- Linux: `dist/GradusFlasher/GradusFlasher`
- Windows после локальной сборки: `dist\GradusFlasher\GradusFlasher.exe`

## Заметки

- Стандартный flash offset: `0x0`
- Приложение оптимизировано под `M5Stick` и похожие устройства на `ESP32`
- Некоторым платам может понадобиться ручной вход в boot/download mode перед прошивкой
- Сейчас доступны профили `Gradus` для `M5Stick S3`, `M5StickC Plus2` и `M5StickC Plus 1.1`
- Под капотом загрузка использует совместимые upstream-бинарники, поэтому реальные имена исходных release-артефактов могут начинаться с `Bruce-`

# Gradus Flasher v0.1.4

Фикс-релиз под реальные логи `esptool 5.2`.

## Что исправлено

- `chip_id` -> `chip-id`
- `flash_id` -> `flash-id`
- `write_flash` -> `write-flash`
- `erase_flash` -> `erase-flash`
- старые флаги `--flash_mode`, `--flash_freq`, `--flash_size` заменены на новые варианты
- исправлен парсинг ответа `ESP32-S3-PICO-1`, `Features` и `MAC`

## Что это дает

- кнопка `Проверить устройство` больше не должна падать на предупреждениях deprecated syntax
- кнопка `Прошить устройство` должна использовать актуальный синтаксис `esptool`

## Артефакты

- Linux: `GradusFlasher-linux-v0.1.4.tar.gz`
- Windows: `GradusFlasher-windows-v0.1.4.zip`
- Windows installer: `GradusFlasher-Setup-v0.1.4.exe`

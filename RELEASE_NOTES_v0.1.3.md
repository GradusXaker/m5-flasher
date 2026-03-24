# Gradus Flasher v0.1.3

Исправляющий релиз для Windows-сборки.

## Что исправлено

- устранена причина дублирования окон приложения в packaged `.exe`
- вызовы `probe`, `analyze` и `flash` больше не запускают новый экземпляр `GradusFlasher`
- интеграция с `esptool` переведена на прямой вызов библиотеки внутри процесса

## Что это значит

- кнопки проверки устройства, анализа прошивки и прошивки должны выполнять свою задачу, а не открывать новое окно программы

## Артефакты

- Linux: `GradusFlasher-linux-v0.1.3.tar.gz`
- Windows: `GradusFlasher-windows-v0.1.3.zip`
- Windows installer: `GradusFlasher-Setup-v0.1.3.exe`

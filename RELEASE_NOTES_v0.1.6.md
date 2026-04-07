# Gradus Flasher v0.1.6

Релиз синхронизации перед следующим циклом поставки прошивок `gradus-firmware`.

Что изменилось:

- версия приложения обновлена до `0.1.6`
- release-ссылки и Windows-артефакты обновлены под `v0.1.6`
- из `windows-release` workflow убран хардкод `v0.1.5`
- installer теперь использует `MyAppVersion` для имени выходного файла

Зачем это нужно:

- следующий релиз `m5-flasher` больше не зависит от вручную прошитого имени installer-файла
- release-процесс лучше совпадает с отдельными firmware-релизами

Ожидаемые артефакты релиза:

- Windows portable: `GradusFlasher-windows-v0.1.6.zip`
- Windows installer: `GradusFlasher-Setup-v0.1.6.exe`

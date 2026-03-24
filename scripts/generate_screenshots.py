from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt

from m5_flasher.branding import create_app_icon
from m5_flasher.ui import FlashWizardDialog, M5FlasherWindow, create_app


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "screenshots"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    app = create_app()
    app.setWindowIcon(create_app_icon())

    window = M5FlasherWindow()
    window.setWindowIcon(create_app_icon())
    window.release_tag_label.setText("Релиз: v0.1.1")
    window.release_update_label.setText("Локальная версия: 0.1.1 | установлена актуальная версия")
    window.release_source_label.setText("Источник: https://github.com/IncursioHack/Bruce")
    window.release_date_label.setText("Дата: 2026-03-24T12:00:00Z")
    window.release_assets_list.clear()
    window.release_assets_list.addItems(
        [
            "GradusFlasher-linux-v0.1.1.tar.gz",
            "GradusFlasher-windows-v0.1.1.zip",
            "Bruce-m5stack-sticks3.bin",
        ]
    )
    window.device_ready = True
    window.firmware_ready = True
    window.device_summary = "Порт: COM7 | Тип чипа: ESP32-S3 | MAC: aa:bb:cc:dd:ee:ff"
    window.firmware_summary = "Файл: Gradus-m5stack-sticks3.bin | Chip ID: ESP32-S3 | Flash size: 8MB"
    window.record_operation("Обновлена информация о релизе v0.1.1")
    window.record_operation("Анализ прошивки выполнен успешно")
    window.record_operation("Устройство успешно определено")
    window._refresh_readiness()
    window.show()
    app.processEvents()
    window.grab().save(str(OUTPUT_DIR / "main-window.png"))

    wizard = FlashWizardDialog(window)
    wizard.step_index = 2
    wizard._render_step()
    wizard.show()
    app.processEvents()
    wizard.grab().save(str(OUTPUT_DIR / "wizard-window.png"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

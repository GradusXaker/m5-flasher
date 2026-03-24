from __future__ import annotations

from pathlib import Path

from m5_flasher.flasher import FirmwareAnalyzeWorker, FlashConfig, FlashWorker, ProbeWorker, run_esptool


def test_run_esptool_image_info_on_real_binary() -> None:
    firmware = Path("downloads/Bruce-m5stack-sticks3.bin")
    lines = run_esptool(["image-info", str(firmware)], lambda line: None)
    assert any("Chip ID:" in line for line in lines)
    assert any("Flash mode:" in line for line in lines)


def test_firmware_analyzer_emits_summary_for_real_binary() -> None:
    firmware = Path("downloads/Bruce-m5stack-sticks3.bin")
    worker = FirmwareAnalyzeWorker(firmware)
    captured: list[tuple[bool, str]] = []
    worker.finished.connect(lambda ok, msg: captured.append((ok, msg)))
    worker.run()
    assert captured
    assert captured[0][0] is True
    assert "Chip ID:" in captured[0][1]


def test_flash_worker_uses_internal_esptool(monkeypatch, tmp_path: Path) -> None:
    firmware = tmp_path / "firmware.bin"
    firmware.write_bytes(b"dummy")

    calls: list[list[str]] = []

    def fake_run_esptool(argv: list[str], on_line):
        calls.append(argv)
        on_line("Writing at 0x00001000... (100 %)")
        return ["Writing at 0x00001000... (100 %)"]

    monkeypatch.setattr("m5_flasher.flasher.run_esptool", fake_run_esptool)

    worker = FlashWorker(FlashConfig(port="COM7", firmware_path=firmware))
    result: list[tuple[bool, str]] = []
    worker.finished.connect(lambda ok, msg: result.append((ok, msg)))
    worker.run()

    assert result == [(True, "Firmware flashed successfully")]
    assert calls
    assert calls[0][0] == "--chip"
    assert calls[0][-1] == str(firmware)


def test_probe_worker_uses_internal_esptool(monkeypatch) -> None:
    responses = {
        "chip-id": [
            "Detecting chip type... ESP32-S3",
            "Chip is ESP32-S3 (QFN56)",
            "MAC: aa:bb:cc:dd:ee:ff",
        ],
        "flash-id": [
            "Detected flash size: 8MB",
        ],
    }

    def fake_run_esptool(argv: list[str], on_line):
        command = argv[-1]
        lines = responses[command]
        for line in lines:
            on_line(line)
        return lines

    monkeypatch.setattr("m5_flasher.flasher.run_esptool", fake_run_esptool)

    worker = ProbeWorker(port="COM7")
    result: list[tuple[bool, str]] = []
    worker.finished.connect(lambda ok, msg: result.append((ok, msg)))
    worker.run()

    assert result
    assert result[0][0] is True
    assert "ESP32-S3" in result[0][1]
    assert "8MB" in result[0][1]


def test_probe_worker_parses_esptool_52_style_output(monkeypatch) -> None:
    responses = {
        "chip-id": [
            "Serial port COM6:",
            "Connecting...",
            "Detecting chip type...",
            " ESP32-S3",
            "Connected to ESP32-S3 on COM6:",
            "Chip type:          ESP32-S3-PICO-1 (LGA56) (revision v0.2)",
            "Features:           Wi-Fi, BT 5 (LE), Dual Core + LP Core, 240MHz, Embedded Flash 8MB (GD), Embedded PSRAM 8MB (AP_3v3)",
            "MAC:                70:04:1d:da:60:70",
        ],
        "flash-id": [
            "Detected flash size: 8MB",
        ],
    }

    def fake_run_esptool(argv: list[str], on_line):
        lines = responses[argv[-1]]
        for line in lines:
            on_line(line)
        return lines

    monkeypatch.setattr("m5_flasher.flasher.run_esptool", fake_run_esptool)

    worker = ProbeWorker(port="COM6", baud_rate=115200)
    result: list[tuple[bool, str]] = []
    worker.finished.connect(lambda ok, msg: result.append((ok, msg)))
    worker.run()

    assert result
    assert result[0][0] is True
    assert "ESP32-S3-PICO-1" in result[0][1]
    assert "Wi-Fi, BT 5" in result[0][1]
    assert "70:04:1d:da:60:70" in result[0][1]

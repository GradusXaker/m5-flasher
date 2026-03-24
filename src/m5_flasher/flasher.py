from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal


PROGRESS_RE = re.compile(r"\(\s*(\d+)\s*%\)")
CHIP_DETECT_RE = re.compile(r"Detecting chip type\.\.\. (.+)")
CHIP_FEATURES_RE = re.compile(r"Chip is (.+)")
MAC_RE = re.compile(r"MAC: ([0-9a-f:]+)", re.IGNORECASE)


@dataclass(slots=True)
class FlashConfig:
    port: str
    firmware_path: Path
    baud_rate: int = 460800
    flash_offset: str = "0x0"
    erase_before_flash: bool = False


class FlashWorker(QObject):
    log = Signal(str)
    progress = Signal(int)
    state = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, config: FlashConfig):
        super().__init__()
        self.config = config
        self._last_lines: list[str] = []

    def run(self) -> None:
        firmware = self.config.firmware_path
        if not firmware.exists():
            self.finished.emit(False, f"Firmware file not found: {firmware}")
            return

        try:
            if self.config.erase_before_flash:
                self._run_command(
                    [
                        sys.executable,
                        "-m",
                        "esptool",
                        "--chip",
                        "auto",
                        "--port",
                        self.config.port,
                        "--baud",
                        str(self.config.baud_rate),
                        "erase_flash",
                    ],
                    "Erasing flash",
                )

            self._run_command(
                [
                    sys.executable,
                    "-m",
                    "esptool",
                    "--chip",
                    "auto",
                    "--port",
                    self.config.port,
                    "--baud",
                    str(self.config.baud_rate),
                    "write_flash",
                    "--flash_mode",
                    "dio",
                    "--flash_freq",
                    "80m",
                    "--flash_size",
                    "keep",
                    self.config.flash_offset,
                    str(firmware),
                ],
                "Flashing firmware",
            )

            self.progress.emit(100)
            self.state.emit("Flash complete")
            self.finished.emit(True, "Firmware flashed successfully")
        except subprocess.CalledProcessError as exc:
            message = "\n".join(self._last_lines[-12:]).strip() or str(exc)
            self.finished.emit(False, message)
        except Exception as exc:  # pragma: no cover - GUI safety path
            self.finished.emit(False, str(exc))

    def _run_command(self, command: list[str], stage_name: str) -> None:
        self.state.emit(stage_name)
        self.log.emit(f"$ {' '.join(command)}")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        assert process.stdout is not None
        for raw_line in process.stdout:
            line = raw_line.rstrip()
            if line:
                self.log.emit(line)
                self._last_lines.append(line)
                if len(self._last_lines) > 200:
                    self._last_lines = self._last_lines[-200:]
                progress_match = PROGRESS_RE.search(line)
                if progress_match:
                    self.progress.emit(int(progress_match.group(1)))

        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)


class ProbeWorker(QObject):
    log = Signal(str)
    state = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, port: str, baud_rate: int = 460800):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self._lines: list[str] = []

    def run(self) -> None:
        try:
            chip_output = self._run_command(
                [
                    sys.executable,
                    "-m",
                    "esptool",
                    "--chip",
                    "auto",
                    "--port",
                    self.port,
                    "--baud",
                    str(self.baud_rate),
                    "chip_id",
                ],
                "Проверка подключения и типа чипа",
            )

            flash_output = self._run_command(
                [
                    sys.executable,
                    "-m",
                    "esptool",
                    "--chip",
                    "auto",
                    "--port",
                    self.port,
                    "--baud",
                    str(self.baud_rate),
                    "flash_id",
                ],
                "Чтение информации о flash",
            )

            summary = self._build_summary(chip_output + flash_output)
            self.state.emit("Проверка устройства завершена")
            self.finished.emit(True, summary)
        except subprocess.CalledProcessError as exc:
            message = "\n".join(self._lines[-12:]).strip() or str(exc)
            self.finished.emit(False, message)
        except Exception as exc:  # pragma: no cover
            self.finished.emit(False, str(exc))

    def _run_command(self, command: list[str], stage_name: str) -> list[str]:
        self.state.emit(stage_name)
        self.log.emit(f"$ {' '.join(command)}")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        lines: list[str] = []
        assert process.stdout is not None
        for raw_line in process.stdout:
            line = raw_line.rstrip()
            if line:
                lines.append(line)
                self._lines.append(line)
                if len(self._lines) > 200:
                    self._lines = self._lines[-200:]
                self.log.emit(line)

        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
        return lines

    def _build_summary(self, lines: list[str]) -> str:
        chip_type = "Не определен"
        chip_info = "Не определено"
        mac = "Не определен"
        flash_size = "Не определен"

        for line in lines:
            if match := CHIP_DETECT_RE.search(line):
                chip_type = match.group(1).strip()
            elif match := CHIP_FEATURES_RE.search(line):
                chip_info = match.group(1).strip()
            elif match := MAC_RE.search(line):
                mac = match.group(1).strip()
            elif "Detected flash size:" in line:
                flash_size = line.split(":", 1)[1].strip()

        return (
            f"Порт: {self.port}\n"
            f"Тип чипа: {chip_type}\n"
            f"Информация о чипе: {chip_info}\n"
            f"MAC: {mac}\n"
            f"Размер flash: {flash_size}"
        )

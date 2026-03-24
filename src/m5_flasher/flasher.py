from __future__ import annotations

import contextlib
import io
import re
from dataclasses import dataclass
from pathlib import Path

import esptool
from PySide6.QtCore import QObject, Signal


PROGRESS_RE = re.compile(r"\(\s*(\d+)\s*%\)")
CHIP_DETECT_RE = re.compile(r"Detecting chip type\.\.\. (.+)")
CHIP_FEATURES_RE = re.compile(r"Chip is (.+)")
CHIP_TYPE_LINE_RE = re.compile(r"Chip type:\s+(.+)")
FEATURES_LINE_RE = re.compile(r"Features:\s+(.+)")
MAC_RE = re.compile(r"MAC:\s+([0-9a-f:]+)", re.IGNORECASE)
ENTRY_RE = re.compile(r"Entry point: (0x[0-9a-fA-F]+)")


class EsptoolError(RuntimeError):
    pass


class _LineEmitter(io.TextIOBase):
    def __init__(self, on_line):
        super().__init__()
        self._on_line = on_line
        self._buffer = ""

    def write(self, text: str) -> int:
        if not text:
            return 0
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            cleaned = line.rstrip()
            if cleaned:
                self._on_line(cleaned)
        return len(text)

    def flush(self) -> None:
        if self._buffer.strip():
            self._on_line(self._buffer.rstrip())
        self._buffer = ""


def run_esptool(argv: list[str], on_line) -> list[str]:
    lines: list[str] = []

    def handle_line(line: str) -> None:
        lines.append(line)
        on_line(line)

    stream = _LineEmitter(handle_line)
    try:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            esptool.main(argv)
        stream.flush()
        return lines
    except SystemExit as exc:  # pragma: no cover - defensive path
        stream.flush()
        if exc.code not in (0, None):
            raise EsptoolError("\n".join(lines[-20:]).strip() or f"esptool exited with code {exc.code}") from exc
        return lines
    except Exception as exc:
        stream.flush()
        message = "\n".join(lines[-20:]).strip() or str(exc)
        raise EsptoolError(message) from exc


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
                        "--chip",
                        "auto",
                        "--port",
                        self.config.port,
                        "--baud",
                        str(self.config.baud_rate),
                        "erase-flash",
                    ],
                    "Erasing flash",
                )

            self._run_command(
                [
                    "--chip",
                    "auto",
                    "--port",
                    self.config.port,
                    "--baud",
                    str(self.config.baud_rate),
                    "write-flash",
                    "--flash-mode",
                    "dio",
                    "--flash-freq",
                    "80m",
                    "--flash-size",
                    "keep",
                    self.config.flash_offset,
                    str(firmware),
                ],
                "Flashing firmware",
            )

            self.progress.emit(100)
            self.state.emit("Flash complete")
            self.finished.emit(True, "Firmware flashed successfully")
        except EsptoolError as exc:
            message = str(exc).strip() or "Unknown esptool error"
            self.finished.emit(False, message)
        except Exception as exc:  # pragma: no cover - GUI safety path
            self.finished.emit(False, str(exc))

    def _run_command(self, argv: list[str], stage_name: str) -> None:
        self.state.emit(stage_name)
        self.log.emit(f"$ esptool {' '.join(argv)}")

        def handle_line(line: str) -> None:
            self.log.emit(line)
            self._last_lines.append(line)
            if len(self._last_lines) > 200:
                self._last_lines = self._last_lines[-200:]
            progress_match = PROGRESS_RE.search(line)
            if progress_match:
                self.progress.emit(int(progress_match.group(1)))

        run_esptool(argv, handle_line)


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
                    "--chip",
                    "auto",
                    "--port",
                    self.port,
                    "--baud",
                    str(self.baud_rate),
                    "chip-id",
                ],
                "Проверка подключения и типа чипа",
            )

            flash_output = self._run_command(
                [
                    "--chip",
                    "auto",
                    "--port",
                    self.port,
                    "--baud",
                    str(self.baud_rate),
                    "flash-id",
                ],
                "Чтение информации о flash",
            )

            summary = self._build_summary(chip_output + flash_output)
            self.state.emit("Проверка устройства завершена")
            self.finished.emit(True, summary)
        except EsptoolError as exc:
            self.finished.emit(False, str(exc).strip() or "Ошибка проверки устройства")
        except Exception as exc:  # pragma: no cover
            self.finished.emit(False, str(exc))

    def _run_command(self, argv: list[str], stage_name: str) -> list[str]:
        self.state.emit(stage_name)
        self.log.emit(f"$ esptool {' '.join(argv)}")

        def handle_line(line: str) -> None:
            self._lines.append(line)
            if len(self._lines) > 200:
                self._lines = self._lines[-200:]
            self.log.emit(line)

        return run_esptool(argv, handle_line)

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
            elif match := CHIP_TYPE_LINE_RE.search(line):
                chip_type = match.group(1).strip()
            elif match := FEATURES_LINE_RE.search(line):
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


class FirmwareAnalyzeWorker(QObject):
    log = Signal(str)
    state = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, firmware_path: Path):
        super().__init__()
        self.firmware_path = firmware_path

    def run(self) -> None:
        if not self.firmware_path.exists():
            self.finished.emit(False, f"Файл не найден: {self.firmware_path}")
            return

        try:
            self.state.emit("Анализ прошивки")
            self.log.emit(f"$ esptool image-info {self.firmware_path}")
            lines = run_esptool(["image-info", str(self.firmware_path)], self.log.emit)
            self.finished.emit(True, self._build_summary(lines))
        except EsptoolError:
            self.finished.emit(False, "Не удалось прочитать image-info для выбранной прошивки")
        except Exception as exc:  # pragma: no cover
            self.finished.emit(False, str(exc))

    def _build_summary(self, lines: list[str]) -> str:
        chip_type = "Не определен"
        flash_mode = "Не определен"
        flash_freq = "Не определена"
        flash_size = "Не определен"
        entry = "Не определен"

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("Chip ID:"):
                chip_type = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Flash size:"):
                flash_size = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Flash freq:"):
                flash_freq = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Flash mode:"):
                flash_mode = stripped.split(":", 1)[1].strip()
            elif match := ENTRY_RE.search(stripped):
                entry = match.group(1)

        return (
            f"Файл: {self.firmware_path.name}\n"
            f"Chip ID: {chip_type}\n"
            f"Flash mode: {flash_mode}\n"
            f"Flash freq: {flash_freq}\n"
            f"Flash size: {flash_size}\n"
            f"Entry point: {entry}"
        )

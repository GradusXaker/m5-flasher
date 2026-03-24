from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QThread, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from m5_flasher.bruce import BRUCE_PROFILES, BruceDownloadWorker
from m5_flasher.flasher import FlashConfig, FlashWorker
from m5_flasher.serial_utils import PortInfo, get_serial_ports
from m5_flasher.styles import APP_STYLESHEET


SETTINGS_ORG = "OpenCode"
SETTINGS_APP = "M5Flasher"
class M5FlasherWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("M5 Flasher // serial console")
        self.resize(1040, 760)

        self.thread: QThread | None = None
        self.worker: FlashWorker | None = None
        self.download_thread: QThread | None = None
        self.download_worker: BruceDownloadWorker | None = None
        self.ports: list[PortInfo] = []
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)

        self._build_ui()
        self.refresh_ports()
        self._load_settings()

    def _build_ui(self) -> None:
        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("M5 FLASHER")
        title.setObjectName("titleLabel")
        subtitle = QLabel("serial upload tool for M5Stick / ESP32 // black terminal edition")
        subtitle.setObjectName("subtitleLabel")

        root.addWidget(title)
        root.addWidget(subtitle)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)
        top_row.addWidget(self._build_flash_panel(), stretch=3)
        top_row.addWidget(self._build_help_panel(), stretch=2)
        root.addLayout(top_row)

        log_group = QGroupBox("Live Output")
        log_layout = QVBoxLayout(log_group)

        self.status_label = QLabel("[idle] waiting for firmware and serial port")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("[log stream will appear here]")

        log_layout.addWidget(self.status_label)
        log_layout.addWidget(self.progress_bar)
        log_layout.addWidget(self.log_output)

        root.addWidget(log_group, stretch=1)
        self.setCentralWidget(container)

    def _build_flash_panel(self) -> QWidget:
        group = QGroupBox("Flash Control")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(320)
        self.port_combo.currentIndexChanged.connect(self._save_settings)
        refresh_button = QPushButton("Refresh Ports")
        refresh_button.clicked.connect(self.refresh_ports)

        self.baud_combo = QComboBox()
        for baud in (115200, 230400, 460800, 921600):
            self.baud_combo.addItem(str(baud), baud)
        self.baud_combo.setCurrentIndex(2)
        self.baud_combo.currentIndexChanged.connect(self._save_settings)

        self.offset_input = QLineEdit("0x0")
        self.offset_input.editingFinished.connect(self._save_settings)

        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Custom firmware file", "")
        for profile in BRUCE_PROFILES:
            self.profile_combo.addItem(profile.label, profile.asset_name)
        self.profile_combo.currentIndexChanged.connect(self._profile_changed)

        self.download_button = QPushButton("Download Latest Bruce")
        self.download_button.clicked.connect(self.download_bruce)

        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select firmware .bin file")
        self.file_input.editingFinished.connect(self._save_settings)
        browse_button = QPushButton("Browse Firmware")
        browse_button.clicked.connect(self.select_firmware)

        self.erase_checkbox = QCheckBox("Erase flash before writing")
        self.erase_checkbox.setChecked(False)
        self.erase_checkbox.stateChanged.connect(self._save_settings)

        self.flash_button = QPushButton("FLASH DEVICE")
        self.flash_button.setObjectName("flashButton")
        self.flash_button.clicked.connect(self.start_flash)

        layout.addWidget(QLabel("Serial Port"), 0, 0)
        layout.addWidget(self.port_combo, 0, 1)
        layout.addWidget(refresh_button, 0, 2)
        layout.addWidget(QLabel("Baud Rate"), 1, 0)
        layout.addWidget(self.baud_combo, 1, 1)
        layout.addWidget(QLabel("Flash Offset"), 2, 0)
        layout.addWidget(self.offset_input, 2, 1)
        layout.addWidget(QLabel("Bruce Profile"), 3, 0)
        layout.addWidget(self.profile_combo, 3, 1)
        layout.addWidget(self.download_button, 3, 2)
        layout.addWidget(QLabel("Firmware File"), 4, 0)
        layout.addWidget(self.file_input, 4, 1)
        layout.addWidget(browse_button, 4, 2)
        layout.addWidget(self.erase_checkbox, 5, 1)
        layout.addWidget(self.flash_button, 6, 1, alignment=Qt.AlignmentFlag.AlignLeft)

        return group

    def _build_help_panel(self) -> QWidget:
        group = QGroupBox("M5Stick Boot Notes")
        layout = QVBoxLayout(group)

        art = QLabel(
            """
+-----------------------+
|  M5Stick upload flow  |
+-----------------------+
| 1. power off device   |
| 2. bridge G0 -> GND   |
| 3. connect USB cable  |
| 4. remove bridge      |
| 5. press FLASH DEVICE |
+-----------------------+
            """.strip()
        )
        art.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        notes = QLabel(
            "If the port does not appear, reconnect the cable or install the USB driver. "
            "For Bruce and many single-image builds, the default offset is 0x0."
        )
        notes.setWordWrap(True)

        layout.addWidget(art)
        layout.addWidget(notes)
        layout.addStretch(1)
        return group

    def refresh_ports(self) -> None:
        selected_port = self.settings.value("selected_port", "", type=str) or self.port_combo.currentData()
        self.ports = get_serial_ports()
        self.port_combo.clear()
        if not self.ports:
            self.port_combo.addItem("No serial ports found", "")
            self.append_log("[warn] no serial ports detected")
            return

        selected_index = 0
        for index, port in enumerate(self.ports):
            self.port_combo.addItem(port.label, port.device)
            if selected_port and port.device == selected_port:
                selected_index = index
        self.port_combo.setCurrentIndex(selected_index)
        self.append_log(f"[info] detected {len(self.ports)} serial port(s)")

    def select_firmware(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select firmware binary",
            str(Path.home()),
            "Firmware (*.bin)",
        )
        if filename:
            self.file_input.setText(filename)
            self.append_log(f"[info] selected firmware: {filename}")
            self._save_settings()

    def start_flash(self) -> None:
        if self.thread is not None or self.download_thread is not None:
            QMessageBox.warning(self, "Flash in progress", "Flashing is already running.")
            return

        port = self.port_combo.currentData()
        firmware_path = self.file_input.text().strip()
        offset = self.offset_input.text().strip() or "0x0"

        if not port:
            QMessageBox.warning(self, "Missing serial port", "Select a serial port first.")
            return

        if not firmware_path:
            QMessageBox.warning(self, "Missing firmware", "Select a firmware .bin file.")
            return

        firmware = Path(firmware_path)
        if not firmware.exists():
            QMessageBox.warning(self, "Firmware not found", f"File does not exist:\n{firmware}")
            return

        config = FlashConfig(
            port=port,
            firmware_path=firmware,
            baud_rate=int(self.baud_combo.currentData()),
            flash_offset=offset,
            erase_before_flash=self.erase_checkbox.isChecked(),
        )

        self.thread = QThread()
        self.worker = FlashWorker(config)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.append_log)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.state.connect(self.update_status)
        self.worker.finished.connect(self.flash_finished)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self._cleanup_thread)

        self.progress_bar.setValue(0)
        self.flash_button.setEnabled(False)
        self.update_status("[flash] starting upload sequence")
        self.append_log(f"[flash] port={config.port} baud={config.baud_rate} offset={config.flash_offset}")
        self._save_settings()
        self.thread.start()

    def download_bruce(self) -> None:
        if self.thread is not None or self.download_thread is not None:
            QMessageBox.warning(self, "Busy", "Wait for the current operation to finish.")
            return

        asset_name = self.profile_combo.currentData()
        if not asset_name:
            QMessageBox.information(self, "Select profile", "Choose a Bruce device profile first.")
            return

        output_dir = Path.home() / "Downloads" / "m5-flasher"
        self.download_thread = QThread()
        self.download_worker = BruceDownloadWorker(asset_name, output_dir)
        self.download_worker.moveToThread(self.download_thread)

        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.log.connect(self.append_log)
        self.download_worker.finished.connect(self._download_finished)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_thread.finished.connect(self._cleanup_download_thread)

        self.flash_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.update_status("[net] downloading latest Bruce firmware")
        self.download_thread.start()

    def flash_finished(self, success: bool, message: str) -> None:
        self.flash_button.setEnabled(True)
        self.download_button.setEnabled(True)
        if success:
            self.update_status("[ok] firmware flashed successfully")
            self.append_log(f"[ok] {message}")
            QMessageBox.information(self, "Flash complete", message)
        else:
            self.update_status("[error] flashing failed")
            self.append_log(f"[error] {message}")
            QMessageBox.critical(self, "Flash failed", message)

    def _cleanup_thread(self) -> None:
        if self.worker is not None:
            self.worker.deleteLater()
        if self.thread is not None:
            self.thread.deleteLater()
        self.worker = None
        self.thread = None

    def _download_finished(self, success: bool, payload: str) -> None:
        self.flash_button.setEnabled(True)
        self.download_button.setEnabled(True)
        if success:
            self.file_input.setText(payload)
            self.update_status("[ok] Bruce firmware downloaded")
            self.append_log(f"[ok] downloaded firmware: {payload}")
            self._save_settings()
            QMessageBox.information(self, "Download complete", f"Bruce firmware saved to:\n{payload}")
        else:
            self.update_status("[error] Bruce download failed")
            self.append_log(f"[error] {payload}")
            QMessageBox.critical(self, "Download failed", payload)

    def _cleanup_download_thread(self) -> None:
        if self.download_worker is not None:
            self.download_worker.deleteLater()
        if self.download_thread is not None:
            self.download_thread.deleteLater()
        self.download_worker = None
        self.download_thread = None

    def append_log(self, line: str) -> None:
        self.log_output.append(line)

    def update_status(self, status: str) -> None:
        self.status_label.setText(status)

    def _profile_changed(self) -> None:
        asset_name = self.profile_combo.currentData()
        if asset_name:
            self.append_log(f"[info] selected Bruce profile: {asset_name}")
        self._save_settings()

    def _load_settings(self) -> None:
        firmware_path = self.settings.value("firmware_path", "", type=str)
        flash_offset = self.settings.value("flash_offset", "0x0", type=str)
        selected_profile = self.settings.value("selected_profile", "", type=str)
        selected_port = self.settings.value("selected_port", "", type=str)
        selected_baud = self.settings.value("baud_rate", 460800, type=int)
        erase_before_flash = self.settings.value("erase_before_flash", False, type=bool)

        if firmware_path:
            self.file_input.setText(firmware_path)
        if flash_offset:
            self.offset_input.setText(flash_offset)
        self.erase_checkbox.setChecked(erase_before_flash)

        baud_index = self.baud_combo.findData(selected_baud)
        if baud_index >= 0:
            self.baud_combo.setCurrentIndex(baud_index)

        profile_index = self.profile_combo.findData(selected_profile)
        if selected_profile and profile_index >= 0:
            self.profile_combo.setCurrentIndex(profile_index)
        elif self.profile_combo.count() > 1:
            self.profile_combo.setCurrentIndex(1)

        if selected_port:
            port_index = self.port_combo.findData(selected_port)
            if port_index >= 0:
                self.port_combo.setCurrentIndex(port_index)

    def _save_settings(self) -> None:
        self.settings.setValue("firmware_path", self.file_input.text().strip())
        self.settings.setValue("flash_offset", self.offset_input.text().strip() or "0x0")
        self.settings.setValue("selected_profile", self.profile_combo.currentData() or "")
        self.settings.setValue("selected_port", self.port_combo.currentData() or "")
        self.settings.setValue("baud_rate", int(self.baud_combo.currentData()))
        self.settings.setValue("erase_before_flash", self.erase_checkbox.isChecked())


def create_app() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(APP_STYLESHEET)
    return app

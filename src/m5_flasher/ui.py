from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QThread, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QDialog,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from m5_flasher.gradus import GRADUS_PROFILES, GradusDownloadWorker, ReleaseInfo, ReleaseInfoWorker, recommend_profile
from m5_flasher.flasher import FirmwareAnalyzeWorker, FlashConfig, FlashWorker, ProbeWorker
from m5_flasher.serial_utils import PortInfo, get_serial_ports
from m5_flasher.styles import APP_STYLESHEET


SETTINGS_ORG = "OpenCode"
SETTINGS_APP = "M5Flasher"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INSTALL_GUIDE = PROJECT_ROOT / "INSTALL.md"
WINDOWS_INSTALL_GUIDE = PROJECT_ROOT / "WINDOWS_INSTALL.md"
MAX_HISTORY_ITEMS = 12


class FlashWizardDialog(QDialog):
    def __init__(self, window: "M5FlasherWindow") -> None:
        super().__init__(window)
        self.window = window
        self.step_index = 0
        self.steps = [
            (
                "Шаг 1. Подключение",
                "Подключи устройство по USB и нажми 'Обновить порты'. Если порт уже появился в списке, переходи дальше.",
            ),
            (
                "Шаг 2. Выбор порта",
                "Выбери правильный serial/COM-порт. Обычно это новый порт, который появился после подключения устройства.",
            ),
            (
                "Шаг 3. Выбор прошивки",
                "Выбери профиль Gradus или укажи свой .bin файл. Для большинства single-image сборок offset должен оставаться 0x0.",
            ),
            (
                "Шаг 4. Boot mode",
                "Если плата не шьется автоматически: выключи устройство, замкни G0 -> GND, подключи USB, убери перемычку и только потом запускай прошивку.",
            ),
            (
                "Шаг 5. Старт",
                "Все готово. Нажми кнопку ниже, чтобы сразу запустить прошивку из мастера.",
            ),
        ]
        self._build_ui()
        self._render_step()

    def _build_ui(self) -> None:
        self.setWindowTitle("Мастер прошивки Gradus")
        self.resize(620, 420)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        self.step_label = QLabel()
        self.step_label.setObjectName("titleLabel")

        self.body_label = QLabel()
        self.body_label.setWordWrap(True)

        self.hint_frame = QFrame()
        hint_layout = QVBoxLayout(self.hint_frame)
        self.hint_label = QLabel()
        self.hint_label.setWordWrap(True)
        hint_layout.addWidget(self.hint_label)

        button_row = QHBoxLayout()
        self.docs_button = QPushButton("Открыть инструкцию")
        self.docs_button.clicked.connect(self.window.open_install_guide)
        self.back_button = QPushButton("Назад")
        self.back_button.clicked.connect(self.prev_step)
        self.next_button = QPushButton("Далее")
        self.next_button.clicked.connect(self.next_step)
        self.flash_now_button = QPushButton("Прошить сейчас")
        self.flash_now_button.setObjectName("flashButton")
        self.flash_now_button.clicked.connect(self.flash_now)
        self.detect_button = QPushButton("Проверить устройство")
        self.detect_button.clicked.connect(self.detect_device)

        button_row.addWidget(self.docs_button)
        button_row.addStretch(1)
        button_row.addWidget(self.detect_button)
        button_row.addWidget(self.back_button)
        button_row.addWidget(self.next_button)
        button_row.addWidget(self.flash_now_button)

        root.addWidget(self.step_label)
        root.addWidget(self.body_label)
        root.addWidget(self.hint_frame)
        root.addStretch(1)
        root.addLayout(button_row)

    def _render_step(self) -> None:
        title, text = self.steps[self.step_index]
        self.step_label.setText(title)
        self.body_label.setText(text)

        hints = {
            0: "Подсказка: если порт не появляется, попробуй другой USB-кабель и нажми 'Обновить порты' в основном окне.",
            1: f"Сейчас выбранный порт: {self.window.port_combo.currentText() or 'не выбран'}.",
            2: f"Текущий профиль: {self.window.profile_combo.currentText()} | файл: {self.window.file_input.text().strip() or 'не выбран'}.",
            3: "Если нужен подробный Windows-only сценарий, открой Windows-гайд из главного окна.",
            4: "После запуска ты увидишь живой лог и прогресс в основном окне приложения.",
        }
        self.hint_label.setText(hints.get(self.step_index, ""))

        self.back_button.setEnabled(self.step_index > 0)
        self.next_button.setEnabled(self.step_index < len(self.steps) - 1)
        self.flash_now_button.setVisible(self.step_index == len(self.steps) - 1)

    def next_step(self) -> None:
        if self.step_index < len(self.steps) - 1:
            self.step_index += 1
            self._render_step()

    def prev_step(self) -> None:
        if self.step_index > 0:
            self.step_index -= 1
            self._render_step()

    def flash_now(self) -> None:
        self.accept()
        self.window.start_flash()

    def detect_device(self) -> None:
        self.window.probe_device()


class M5FlasherWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Gradus Flasher // serial console")
        self.resize(1040, 760)

        self.thread: QThread | None = None
        self.worker: FlashWorker | None = None
        self.probe_thread: QThread | None = None
        self.probe_worker: ProbeWorker | None = None
        self.analyze_thread: QThread | None = None
        self.analyze_worker: FirmwareAnalyzeWorker | None = None
        self.download_thread: QThread | None = None
        self.download_worker: GradusDownloadWorker | None = None
        self.release_thread: QThread | None = None
        self.release_worker: ReleaseInfoWorker | None = None
        self.ports: list[PortInfo] = []
        self.device_ready = False
        self.firmware_ready = False
        self.device_summary = "Устройство еще не проверено"
        self.firmware_summary = "Прошивка еще не проверена"
        self.operation_history: list[str] = []
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)

        self._build_ui()
        self.refresh_ports()
        self._load_settings()
        self._refresh_readiness()
        app = QApplication.instance()
        if app is not None and app.platformName() != "offscreen":
            self.refresh_release_info()
        self._schedule_onboarding()

    def _build_ui(self) -> None:
        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("GRADUS FLASHER")
        title.setObjectName("titleLabel")
        subtitle = QLabel("прошивальщик для M5Stick / ESP32 // black terminal edition")
        subtitle.setObjectName("subtitleLabel")

        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        open_install_button = QPushButton("Открыть инструкцию")
        open_install_button.clicked.connect(self.open_install_guide)
        open_windows_install_button = QPushButton("Windows-гайд")
        open_windows_install_button.clicked.connect(self.open_windows_install_guide)
        open_wizard_button = QPushButton("Мастер прошивки")
        open_wizard_button.clicked.connect(self.show_flash_wizard)
        show_onboarding_button = QPushButton("Показать onboarding")
        show_onboarding_button.clicked.connect(self.show_onboarding)
        actions_row.addWidget(open_install_button)
        actions_row.addWidget(open_windows_install_button)
        actions_row.addWidget(open_wizard_button)
        actions_row.addWidget(show_onboarding_button)
        actions_row.addStretch(1)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(actions_row)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)
        top_row.addWidget(self._build_flash_panel(), stretch=3)
        right_column = QVBoxLayout()
        right_column.setSpacing(14)
        right_column.addWidget(self._build_help_panel(), stretch=1)
        right_column.addWidget(self._build_release_panel(), stretch=1)
        right_column.addWidget(self._build_history_panel(), stretch=1)
        top_row.addLayout(right_column, stretch=2)
        root.addLayout(top_row)

        root.addWidget(self._build_status_panel())

        log_group = QGroupBox("Живой лог")
        log_layout = QVBoxLayout(log_group)

        self.status_label = QLabel("[idle] ожидание прошивки и serial-порта")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("[здесь появится поток логов]")

        log_layout.addWidget(self.status_label)
        log_layout.addWidget(self.progress_bar)
        log_layout.addWidget(self.log_output)

        root.addWidget(log_group, stretch=1)
        self.setCentralWidget(container)

    def _build_flash_panel(self) -> QWidget:
        group = QGroupBox("Управление прошивкой")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(320)
        self.port_combo.currentIndexChanged.connect(self._save_settings)
        self.port_combo.currentIndexChanged.connect(self._port_changed)
        refresh_button = QPushButton("Обновить порты")
        refresh_button.clicked.connect(self.refresh_ports)

        self.baud_combo = QComboBox()
        for baud in (115200, 230400, 460800, 921600):
            self.baud_combo.addItem(str(baud), baud)
        self.baud_combo.setCurrentIndex(2)
        self.baud_combo.currentIndexChanged.connect(self._save_settings)

        self.offset_input = QLineEdit("0x0")
        self.offset_input.editingFinished.connect(self._save_settings)

        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Свой файл прошивки", "")
        for profile in GRADUS_PROFILES:
            self.profile_combo.addItem(profile.label, profile.asset_name)
        self.profile_combo.currentIndexChanged.connect(self._profile_changed)

        self.download_button = QPushButton("Скачать последний Gradus")
        self.download_button.clicked.connect(self.download_gradus)

        self.probe_button = QPushButton("Проверить устройство")
        self.probe_button.clicked.connect(self.probe_device)

        self.analyze_button = QPushButton("Анализ .bin")
        self.analyze_button.clicked.connect(self.analyze_firmware)

        self.recommendation_label = QLabel("Рекомендация профиля: еще не определена")
        self.recommendation_label.setWordWrap(True)

        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Выбери файл прошивки .bin")
        self.file_input.editingFinished.connect(self._save_settings)
        self.file_input.editingFinished.connect(self._firmware_changed)
        browse_button = QPushButton("Открыть файл")
        browse_button.clicked.connect(self.select_firmware)

        self.erase_checkbox = QCheckBox("Стереть flash перед записью")
        self.erase_checkbox.setChecked(False)
        self.erase_checkbox.stateChanged.connect(self._save_settings)

        self.flash_button = QPushButton("ПРОШИТЬ УСТРОЙСТВО")
        self.flash_button.setObjectName("flashButton")
        self.flash_button.clicked.connect(self.start_flash)

        layout.addWidget(QLabel("Serial-порт"), 0, 0)
        layout.addWidget(self.port_combo, 0, 1)
        layout.addWidget(refresh_button, 0, 2)
        layout.addWidget(QLabel("Скорость baud"), 1, 0)
        layout.addWidget(self.baud_combo, 1, 1)
        layout.addWidget(QLabel("Смещение flash"), 2, 0)
        layout.addWidget(self.offset_input, 2, 1)
        layout.addWidget(QLabel("Профиль Gradus"), 3, 0)
        layout.addWidget(self.profile_combo, 3, 1)
        layout.addWidget(self.download_button, 3, 2)
        layout.addWidget(QLabel("Файл прошивки"), 4, 0)
        layout.addWidget(self.file_input, 4, 1)
        layout.addWidget(browse_button, 4, 2)
        layout.addWidget(self.recommendation_label, 5, 0, 1, 3)
        layout.addWidget(self.erase_checkbox, 6, 1)
        layout.addWidget(self.probe_button, 7, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.analyze_button, 7, 2, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.flash_button, 8, 2, alignment=Qt.AlignmentFlag.AlignLeft)

        return group

    def _build_status_panel(self) -> QWidget:
        group = QGroupBox("Готовность к прошивке")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(8)

        self.ready_badge = QLabel("НЕ ГОТОВО")
        self.ready_badge.setObjectName("titleLabel")

        self.device_state_label = QLabel("Устройство: не проверено")
        self.device_state_label.setWordWrap(True)
        self.firmware_state_label = QLabel("Прошивка: не проверена")
        self.firmware_state_label.setWordWrap(True)
        self.summary_state_label = QLabel("Статус: выбери порт, проверь устройство и проанализируй .bin")
        self.summary_state_label.setWordWrap(True)

        layout.addWidget(self.ready_badge, 0, 0)
        layout.addWidget(self.summary_state_label, 0, 1)
        layout.addWidget(self.device_state_label, 1, 0, 1, 2)
        layout.addWidget(self.firmware_state_label, 2, 0, 1, 2)
        return group

    def _build_help_panel(self) -> QWidget:
        group = QGroupBox("Подсказка по M5Stick")
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
            "Если порт не появился, переподключи кабель или установи USB-драйвер. "
            "Для Gradus и большинства single-image сборок стандартный offset: 0x0."
        )
        notes.setWordWrap(True)

        open_docs_button = QPushButton("Открыть инструкции")
        open_docs_button.clicked.connect(self.open_install_guide)

        open_windows_docs_button = QPushButton("Открыть Windows-гайд")
        open_windows_docs_button.clicked.connect(self.open_windows_install_guide)

        open_wizard_button = QPushButton("Запустить мастер")
        open_wizard_button.clicked.connect(self.show_flash_wizard)

        layout.addWidget(art)
        layout.addWidget(notes)
        layout.addWidget(open_docs_button)
        layout.addWidget(open_windows_docs_button)
        layout.addWidget(open_wizard_button)
        layout.addStretch(1)
        return group

    def _build_release_panel(self) -> QWidget:
        group = QGroupBox("Центр релизов Gradus")
        layout = QVBoxLayout(group)

        self.release_tag_label = QLabel("Релиз: загрузка...")
        self.release_tag_label.setObjectName("panelTitleLabel")
        self.release_source_label = QLabel("Источник: upstream release feed")
        self.release_source_label.setWordWrap(True)
        self.release_date_label = QLabel("Дата: неизвестно")
        self.release_date_label.setWordWrap(True)

        self.release_assets_list = QListWidget()
        self.release_assets_list.setAlternatingRowColors(True)

        refresh_release_button = QPushButton("Обновить релиз")
        refresh_release_button.clicked.connect(self.refresh_release_info)

        layout.addWidget(self.release_tag_label)
        layout.addWidget(self.release_source_label)
        layout.addWidget(self.release_date_label)
        layout.addWidget(self.release_assets_list)
        layout.addWidget(refresh_release_button)
        return group

    def _build_history_panel(self) -> QWidget:
        group = QGroupBox("История операций")
        layout = QVBoxLayout(group)

        self.history_list = QListWidget()
        self.history_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        clear_button = QPushButton("Очистить историю")
        clear_button.clicked.connect(self.clear_history)

        layout.addWidget(self.history_list)
        layout.addWidget(clear_button)
        return group

    def refresh_ports(self) -> None:
        selected_port = self.settings.value("selected_port", "", type=str) or self.port_combo.currentData()
        self.ports = get_serial_ports()
        self.port_combo.clear()
        if not self.ports:
            self.port_combo.addItem("Serial-порты не найдены", "")
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
            "Выбор файла прошивки",
            str(Path.home()),
            "Firmware (*.bin)",
        )
        if filename:
            self.file_input.setText(filename)
            self.append_log(f"[info] selected firmware: {filename}")
            self.firmware_ready = False
            self.firmware_summary = "Прошивка выбрана, но еще не проанализирована"
            self.record_operation(f"Выбран файл прошивки: {Path(filename).name}")
            self._refresh_readiness()
            self._save_settings()

    def analyze_firmware(self) -> None:
        if (
            self.thread is not None
            or self.download_thread is not None
            or self.probe_thread is not None
            or self.analyze_thread is not None
        ):
            QMessageBox.warning(self, "Занято", "Дождись завершения текущей операции.")
            return

        firmware_path = self.file_input.text().strip()
        if not firmware_path:
            QMessageBox.warning(self, "Не выбрана прошивка", "Сначала выбери файл прошивки .bin.")
            return

        firmware = Path(firmware_path)
        if not firmware.exists():
            QMessageBox.warning(self, "Файл не найден", f"Файл не существует:\n{firmware}")
            return

        if not self.device_ready or not self.firmware_ready:
            answer = QMessageBox.question(
                self,
                "Подтвердить прошивку",
                "Устройство или прошивка еще не проверены полностью. Все равно продолжить?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.analyze_thread = QThread()
        self.analyze_worker = FirmwareAnalyzeWorker(firmware)
        self.analyze_worker.moveToThread(self.analyze_thread)

        self.analyze_thread.started.connect(self.analyze_worker.run)
        self.analyze_worker.log.connect(self.append_log)
        self.analyze_worker.state.connect(self.update_status)
        self.analyze_worker.finished.connect(self._analyze_finished)
        self.analyze_worker.finished.connect(self.analyze_thread.quit)
        self.analyze_thread.finished.connect(self._cleanup_analyze_thread)

        self.flash_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.probe_button.setEnabled(False)
        self.analyze_button.setEnabled(False)
        self.update_status("[analyze] анализ выбранной прошивки")
        self.append_log(f"[analyze] firmware={firmware}")
        self.analyze_thread.start()

    def refresh_release_info(self) -> None:
        if self.release_thread is not None:
            return

        self.release_thread = QThread()
        self.release_worker = ReleaseInfoWorker()
        self.release_worker.moveToThread(self.release_thread)

        self.release_thread.started.connect(self.release_worker.run)
        self.release_worker.log.connect(self.append_log)
        self.release_worker.finished.connect(self._release_info_finished)
        self.release_worker.finished.connect(self.release_thread.quit)
        self.release_thread.finished.connect(self._cleanup_release_thread)
        self.release_thread.start()

    def start_flash(self) -> None:
        if (
            self.thread is not None
            or self.download_thread is not None
            or self.probe_thread is not None
            or self.analyze_thread is not None
        ):
            QMessageBox.warning(self, "Прошивка уже идет", "Операция прошивки уже запущена.")
            return

        port = self.port_combo.currentData()
        firmware_path = self.file_input.text().strip()
        offset = self.offset_input.text().strip() or "0x0"

        if not port:
            QMessageBox.warning(self, "Не выбран порт", "Сначала выбери serial-порт.")
            return

        if not firmware_path:
            QMessageBox.warning(self, "Не выбрана прошивка", "Выбери файл прошивки .bin.")
            return

        firmware = Path(firmware_path)
        if not firmware.exists():
            QMessageBox.warning(self, "Файл не найден", f"Файл не существует:\n{firmware}")
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
        self.download_button.setEnabled(False)
        self.probe_button.setEnabled(False)
        self.analyze_button.setEnabled(False)
        self.update_status("[flash] запуск последовательности прошивки")
        self.append_log(f"[flash] port={config.port} baud={config.baud_rate} offset={config.flash_offset}")
        self._save_settings()
        self.thread.start()

    def download_gradus(self) -> None:
        if (
            self.thread is not None
            or self.download_thread is not None
            or self.probe_thread is not None
            or self.analyze_thread is not None
        ):
            QMessageBox.warning(self, "Занято", "Дождись завершения текущей операции.")
            return

        asset_name = self.profile_combo.currentData()
        if not asset_name:
            QMessageBox.information(self, "Выбери профиль", "Сначала выбери профиль Gradus для устройства.")
            return

        output_dir = Path.home() / "Downloads" / "m5-flasher"
        self.download_thread = QThread()
        self.download_worker = GradusDownloadWorker(asset_name, output_dir)
        self.download_worker.moveToThread(self.download_thread)

        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.log.connect(self.append_log)
        self.download_worker.finished.connect(self._download_finished)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_thread.finished.connect(self._cleanup_download_thread)

        self.flash_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.probe_button.setEnabled(False)
        self.analyze_button.setEnabled(False)
        self.update_status("[net] загрузка последней прошивки Gradus")
        self.download_thread.start()

    def probe_device(self) -> None:
        if (
            self.thread is not None
            or self.download_thread is not None
            or self.probe_thread is not None
            or self.analyze_thread is not None
        ):
            QMessageBox.warning(self, "Занято", "Дождись завершения текущей операции.")
            return

        port = self.port_combo.currentData()
        if not port:
            QMessageBox.warning(self, "Не выбран порт", "Сначала выбери serial-порт.")
            return

        self.probe_thread = QThread()
        self.probe_worker = ProbeWorker(port=port, baud_rate=int(self.baud_combo.currentData()))
        self.probe_worker.moveToThread(self.probe_thread)

        self.probe_thread.started.connect(self.probe_worker.run)
        self.probe_worker.log.connect(self.append_log)
        self.probe_worker.state.connect(self.update_status)
        self.probe_worker.finished.connect(self._probe_finished)
        self.probe_worker.finished.connect(self.probe_thread.quit)
        self.probe_thread.finished.connect(self._cleanup_probe_thread)

        self.flash_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.probe_button.setEnabled(False)
        self.analyze_button.setEnabled(False)
        self.update_status("[probe] проверка подключения устройства")
        self.append_log(f"[probe] port={port} baud={int(self.baud_combo.currentData())}")
        self.probe_thread.start()

    def flash_finished(self, success: bool, message: str) -> None:
        self.flash_button.setEnabled(True)
        self.download_button.setEnabled(True)
        self.probe_button.setEnabled(True)
        self.analyze_button.setEnabled(True)
        if success:
            self.update_status("[ok] firmware flashed successfully")
            self.append_log(f"[ok] {message}")
            self.record_operation("Прошивка устройства завершена успешно")
            QMessageBox.information(self, "Прошивка завершена", message)
        else:
            self.update_status("[error] flashing failed")
            self.append_log(f"[error] {message}")
            self.record_operation("Ошибка во время прошивки устройства")
            QMessageBox.critical(self, "Ошибка прошивки", message)

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
        self.probe_button.setEnabled(True)
        self.analyze_button.setEnabled(True)
        if success:
            self.file_input.setText(payload)
            self.update_status("[ok] прошивка Gradus загружена")
            self.append_log(f"[ok] downloaded firmware: {payload}")
            self.record_operation(f"Загружена прошивка: {Path(payload).name}")
            self.firmware_ready = False
            self.firmware_summary = "Прошивка загружена, но еще не проанализирована"
            self._refresh_readiness()
            self._save_settings()
            QMessageBox.information(self, "Загрузка завершена", f"Прошивка Gradus сохранена в:\n{payload}")
        else:
            self.update_status("[error] ошибка загрузки Gradus")
            self.append_log(f"[error] {payload}")
            QMessageBox.critical(self, "Ошибка загрузки", payload)

    def _probe_finished(self, success: bool, payload: str) -> None:
        self.flash_button.setEnabled(True)
        self.download_button.setEnabled(True)
        self.probe_button.setEnabled(True)
        self.analyze_button.setEnabled(True)
        if success:
            self.update_status("[ok] устройство обнаружено")
            self.append_log(f"[ok] {payload}")
            self.record_operation("Устройство успешно определено")
            self.device_ready = True
            self.device_summary = payload
            self._apply_profile_recommendation(payload)
            self._refresh_readiness()
            QMessageBox.information(self, "Устройство найдено", payload)
        else:
            self.update_status("[error] устройство не ответило")
            self.append_log(f"[error] {payload}")
            self.record_operation("Ошибка проверки подключения устройства")
            self.device_ready = False
            self.device_summary = payload
            self.recommendation_label.setText("Рекомендация профиля: не удалось проверить устройство")
            self._refresh_readiness()
            QMessageBox.critical(self, "Ошибка проверки", payload)

    def _analyze_finished(self, success: bool, payload: str) -> None:
        self.flash_button.setEnabled(True)
        self.download_button.setEnabled(True)
        self.probe_button.setEnabled(True)
        self.analyze_button.setEnabled(True)
        if success:
            self.update_status("[ok] прошивка проанализирована")
            self.append_log(f"[ok] {payload}")
            self.record_operation("Анализ прошивки выполнен успешно")
            self.firmware_ready = True
            self.firmware_summary = payload
            self._refresh_readiness()
            QMessageBox.information(self, "Анализ прошивки", payload)
        else:
            self.update_status("[error] анализ прошивки не удался")
            self.append_log(f"[error] {payload}")
            self.record_operation("Ошибка анализа прошивки")
            self.firmware_ready = False
            self.firmware_summary = payload
            self._refresh_readiness()
            QMessageBox.critical(self, "Ошибка анализа", payload)

    def _cleanup_download_thread(self) -> None:
        if self.download_worker is not None:
            self.download_worker.deleteLater()
        if self.download_thread is not None:
            self.download_thread.deleteLater()
        self.download_worker = None
        self.download_thread = None

    def _cleanup_probe_thread(self) -> None:
        if self.probe_worker is not None:
            self.probe_worker.deleteLater()
        if self.probe_thread is not None:
            self.probe_thread.deleteLater()
        self.probe_worker = None
        self.probe_thread = None

    def _cleanup_analyze_thread(self) -> None:
        if self.analyze_worker is not None:
            self.analyze_worker.deleteLater()
        if self.analyze_thread is not None:
            self.analyze_thread.deleteLater()
        self.analyze_worker = None
        self.analyze_thread = None

    def _release_info_finished(self, success: bool, payload: object) -> None:
        if success and isinstance(payload, ReleaseInfo):
            self.release_tag_label.setText(f"Релиз: {payload.tag_name}")
            self.release_source_label.setText(f"Источник: {payload.source_url}")
            self.release_date_label.setText(f"Дата: {payload.published_at}")
            self.release_assets_list.clear()
            self.release_assets_list.addItems(payload.asset_names)
            self.append_log(f"[ok] release {payload.tag_name} loaded with {len(payload.asset_names)} asset(s)")
            self.record_operation(f"Обновлена информация о релизе {payload.tag_name}")
        else:
            self.release_tag_label.setText("Релиз: ошибка загрузки")
            self.release_source_label.setText("Источник: недоступен")
            self.release_date_label.setText(str(payload))
            self.release_assets_list.clear()

    def _cleanup_release_thread(self) -> None:
        if self.release_worker is not None:
            self.release_worker.deleteLater()
        if self.release_thread is not None:
            self.release_thread.deleteLater()
        self.release_worker = None
        self.release_thread = None

    def append_log(self, line: str) -> None:
        self.log_output.append(line)

    def update_status(self, status: str) -> None:
        self.status_label.setText(status)

    def _refresh_readiness(self) -> None:
        self.device_state_label.setText(
            f"Устройство: {'готово' if self.device_ready else 'не готово'} | {self._shorten(self.device_summary)}"
        )
        self.firmware_state_label.setText(
            f"Прошивка: {'готова' if self.firmware_ready else 'не готова'} | {self._shorten(self.firmware_summary)}"
        )

        if self.device_ready and self.firmware_ready:
            self.ready_badge.setText("ГОТОВО")
            self.summary_state_label.setText("Статус: можно запускать прошивку")
        else:
            self.ready_badge.setText("НЕ ГОТОВО")
            missing: list[str] = []
            if not self.device_ready:
                missing.append("проверка устройства")
            if not self.firmware_ready:
                missing.append("анализ .bin")
            self.summary_state_label.setText(f"Статус: сначала выполни {', '.join(missing)}")

    def _shorten(self, text: str, limit: int = 110) -> str:
        single_line = " ".join(text.splitlines())
        if len(single_line) <= limit:
            return single_line
        return single_line[: limit - 3] + "..."

    def open_install_guide(self) -> None:
        self._open_local_guide(INSTALL_GUIDE, "Не удалось открыть INSTALL.md")

    def open_windows_install_guide(self) -> None:
        self._open_local_guide(WINDOWS_INSTALL_GUIDE, "Не удалось открыть WINDOWS_INSTALL.md")

    def show_flash_wizard(self) -> None:
        dialog = FlashWizardDialog(self)
        dialog.exec()

    def _open_local_guide(self, guide_path: Path, error_title: str) -> None:
        if not guide_path.exists():
            QMessageBox.warning(self, error_title, f"Файл не найден:\n{guide_path}")
            return

        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(guide_path)))
        if not opened:
            QMessageBox.warning(self, error_title, f"Открой файл вручную:\n{guide_path}")

    def record_operation(self, message: str) -> None:
        entry = message.strip()
        if not entry:
            return
        self.operation_history.insert(0, entry)
        self.operation_history = self.operation_history[:MAX_HISTORY_ITEMS]
        self.history_list.clear()
        self.history_list.addItems(self.operation_history)
        self.settings.setValue("operation_history", self.operation_history)

    def clear_history(self) -> None:
        self.operation_history = []
        self.history_list.clear()
        self.settings.setValue("operation_history", self.operation_history)

    def _schedule_onboarding(self) -> None:
        already_seen = self.settings.value("onboarding_seen", False, type=bool)
        app = QApplication.instance()
        if already_seen or app is None or app.platformName() == "offscreen":
            return
        QTimer.singleShot(200, self.show_onboarding)

    def show_onboarding(self) -> None:
        self.settings.setValue("onboarding_seen", True)
        message = (
            "Добро пожаловать в Gradus Flasher.\n\n"
            "Быстрый старт:\n"
            "1. Подключи M5Stick по USB.\n"
            "2. Нажми 'Обновить порты'.\n"
            "3. Выбери serial/COM-порт.\n"
            "4. Выбери профиль Gradus или свой .bin.\n"
            "5. При необходимости нажми 'Скачать последний Gradus'.\n"
            "6. Нажми 'ПРОШИТЬ УСТРОЙСТВО'.\n\n"
            "Если плата не шьется, сначала открой инструкцию и проверь boot mode."
        )

        box = QMessageBox(self)
        box.setWindowTitle("Первый запуск Gradus")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(message)
        install_button = box.addButton("Открыть инструкцию", QMessageBox.ButtonRole.ActionRole)
        windows_button = box.addButton("Windows-гайд", QMessageBox.ButtonRole.ActionRole)
        ok_button = box.addButton("Продолжить", QMessageBox.ButtonRole.AcceptRole)
        box.setDefaultButton(ok_button)
        box.exec()

        clicked = box.clickedButton()
        if clicked == install_button:
            self.open_install_guide()
        elif clicked == windows_button:
            self.open_windows_install_guide()

    def _profile_changed(self) -> None:
        asset_name = self.profile_combo.currentData()
        if asset_name:
            self.append_log(f"[info] выбран профиль Gradus: {asset_name}")
        self._save_settings()

    def _port_changed(self) -> None:
        self.device_ready = False
        self.device_summary = "Устройство еще не проверено после смены порта"
        self._refresh_readiness()

    def _firmware_changed(self) -> None:
        self.firmware_ready = False
        self.firmware_summary = "Прошивка изменена и требует нового анализа"
        self._refresh_readiness()

    def _apply_profile_recommendation(self, probe_summary: str) -> None:
        chip_type = self._extract_probe_field(probe_summary, "Тип чипа")
        chip_info = self._extract_probe_field(probe_summary, "Информация о чипе")
        recommendation = recommend_profile(chip_type, chip_info)

        if recommendation.auto_select and recommendation.profile_asset:
            profile_index = self.profile_combo.findData(recommendation.profile_asset)
            if profile_index >= 0:
                self.profile_combo.setCurrentIndex(profile_index)
                selected_text = self.profile_combo.itemText(profile_index)
                self.recommendation_label.setText(
                    f"Рекомендация профиля: автоматически выбран {selected_text}"
                )
                self.append_log(f"[info] авто выбран профиль: {recommendation.profile_asset}")
                return

        self.recommendation_label.setText(f"Рекомендация профиля: {recommendation.message}")
        self.append_log(f"[info] {recommendation.title}: {recommendation.message}")

    def _extract_probe_field(self, probe_summary: str, field_name: str) -> str:
        prefix = f"{field_name}:"
        for line in probe_summary.splitlines():
            if line.startswith(prefix):
                return line.split(":", 1)[1].strip()
        return ""

    def _load_settings(self) -> None:
        firmware_path = self.settings.value("firmware_path", "", type=str)
        flash_offset = self.settings.value("flash_offset", "0x0", type=str)
        selected_profile = self.settings.value("selected_profile", "", type=str)
        selected_port = self.settings.value("selected_port", "", type=str)
        selected_baud = self.settings.value("baud_rate", 460800, type=int)
        erase_before_flash = self.settings.value("erase_before_flash", False, type=bool)
        operation_history = self.settings.value("operation_history", [], type=list)

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

        self.operation_history = [str(item) for item in operation_history][:MAX_HISTORY_ITEMS]
        self.history_list.clear()
        self.history_list.addItems(self.operation_history)

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

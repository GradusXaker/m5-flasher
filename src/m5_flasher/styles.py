APP_STYLESHEET = """
QWidget {
    background-color: #050805;
    color: #77ff77;
    font-family: "DejaVu Sans Mono";
    font-size: 13px;
}

QMainWindow, QFrame {
    background-color: #050805;
}

QLabel#titleLabel {
    color: #9dff9d;
    font-size: 28px;
    font-weight: bold;
}

QLabel#subtitleLabel {
    color: #49d349;
    font-size: 12px;
}

QGroupBox {
    border: 1px solid #1f7a1f;
    margin-top: 14px;
    padding-top: 16px;
    border-radius: 8px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #8eff8e;
}

QPushButton {
    background-color: #081508;
    border: 1px solid #1fa31f;
    border-radius: 8px;
    padding: 10px 14px;
    color: #9cff9c;
}

QPushButton:hover {
    background-color: #0d250d;
}

QPushButton:pressed {
    background-color: #103010;
}

QPushButton#flashButton {
    background-color: #103d10;
    font-weight: bold;
}

QLineEdit, QComboBox, QTextEdit {
    background-color: #061106;
    border: 1px solid #1a6d1a;
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #1f7a1f;
    color: #a8ffa8;
}

QComboBox QAbstractItemView {
    background-color: #061106;
    color: #a8ffa8;
    selection-background-color: #103d10;
}

QProgressBar {
    border: 1px solid #1f7a1f;
    border-radius: 6px;
    text-align: center;
    background-color: #061106;
    color: #d7ffd7;
}

QProgressBar::chunk {
    background-color: #23c323;
    border-radius: 5px;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    border: 1px solid #1f7a1f;
    background-color: #061106;
}

QCheckBox::indicator:checked {
    border: 1px solid #1f7a1f;
    background-color: #23c323;
}
"""

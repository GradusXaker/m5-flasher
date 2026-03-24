from __future__ import annotations

from PySide6.QtCore import QByteArray
from PySide6.QtGui import QIcon, QPixmap


GRADUS_ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="28" fill="#050805"/>
  <rect x="18" y="18" width="220" height="220" rx="20" fill="none" stroke="#1fa31f" stroke-width="6"/>
  <path d="M64 188 L96 68 L126 68 L94 188 Z" fill="#8eff8e"/>
  <path d="M118 188 L150 68 L180 68 L148 188 Z" fill="#49d349"/>
  <rect x="62" y="196" width="126" height="12" rx="6" fill="#23c323"/>
  <path d="M174 58 L198 82 L174 106" fill="none" stroke="#9dff9d" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M84 118 L62 138 L84 158" fill="none" stroke="#9dff9d" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
""".strip()


def create_app_icon() -> QIcon:
    pixmap = QPixmap()
    pixmap.loadFromData(QByteArray(GRADUS_ICON_SVG.encode("utf-8")), "SVG")
    return QIcon(pixmap)

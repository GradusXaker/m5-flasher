from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal


LATEST_RELEASE_URL = "https://api.github.com/repos/BruceDevices/firmware/releases/latest"


@dataclass(slots=True)
class BruceProfile:
    label: str
    asset_name: str
    note: str


BRUCE_PROFILES = [
    BruceProfile("Bruce // M5Stick S3", "Bruce-m5stack-sticks3.bin", "Recommended for M5Stick S3"),
    BruceProfile("Bruce // M5StickC Plus2", "Bruce-m5stack-cplus2.bin", "For M5StickC Plus2"),
    BruceProfile("Bruce // M5StickC Plus 1.1", "Bruce-m5stack-cplus1_1.bin", "For M5StickC Plus 1.1"),
]


class BruceDownloadWorker(QObject):
    log = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, asset_name: str, output_dir: Path):
        super().__init__()
        self.asset_name = asset_name
        self.output_dir = output_dir

    def run(self) -> None:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.log.emit(f"[net] loading Bruce release metadata for {self.asset_name}")

            request = urllib.request.Request(
                LATEST_RELEASE_URL,
                headers={"User-Agent": "m5-flasher"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)

            asset = next((item for item in payload.get("assets", []) if item.get("name") == self.asset_name), None)
            if asset is None:
                raise RuntimeError(f"Asset not found in latest Bruce release: {self.asset_name}")

            release_tag = payload.get("tag_name", "latest")
            destination = self.output_dir / asset["name"]
            self.log.emit(f"[net] downloading Bruce {release_tag} -> {destination}")
            urllib.request.urlretrieve(asset["browser_download_url"], destination)
            self.finished.emit(True, str(destination))
        except Exception as exc:  # pragma: no cover - network path
            self.finished.emit(False, str(exc))

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal


SOURCE_REPO_URL = "https://github.com/IncursioHack/Bruce"
LATEST_RELEASE_URL = "https://api.github.com/repos/BruceDevices/firmware/releases/latest"


@dataclass(slots=True)
class GradusProfile:
    label: str
    asset_name: str
    note: str


@dataclass(slots=True)
class ProfileRecommendation:
    profile_asset: str | None
    title: str
    message: str
    auto_select: bool


GRADUS_PROFILES = [
    GradusProfile("Gradus // M5Stick S3", "Bruce-m5stack-sticks3.bin", "Recommended for M5Stick S3"),
    GradusProfile("Gradus // M5StickC Plus2", "Bruce-m5stack-cplus2.bin", "For M5StickC Plus2"),
    GradusProfile("Gradus // M5StickC Plus 1.1", "Bruce-m5stack-cplus1_1.bin", "For M5StickC Plus 1.1"),
]


def recommend_profile(chip_type: str, chip_info: str) -> ProfileRecommendation:
    normalized = f"{chip_type} {chip_info}".lower()

    if "esp32-s3" in normalized:
        return ProfileRecommendation(
            profile_asset="Bruce-m5stack-sticks3.bin",
            title="Найден профиль для ESP32-S3",
            message="Обнаружен чип семейства ESP32-S3. Для поддерживаемых профилей это однозначно похоже на M5Stick S3, профиль можно выбрать автоматически.",
            auto_select=True,
        )

    if "esp32" in normalized:
        return ProfileRecommendation(
            profile_asset=None,
            title="Найдено несколько вариантов профиля",
            message="Обнаружен чип семейства ESP32. Для поддерживаемых M5Stick это обычно Gradus // M5StickC Plus2 или Gradus // M5StickC Plus 1.1, поэтому профиль лучше выбрать вручную.",
            auto_select=False,
        )

    return ProfileRecommendation(
        profile_asset=None,
        title="Профиль не определен автоматически",
        message="Тип чипа удалось прочитать, но для него пока нет однозначного автоподбора среди встроенных профилей Gradus.",
        auto_select=False,
    )


class GradusDownloadWorker(QObject):
    log = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, asset_name: str, output_dir: Path):
        super().__init__()
        self.asset_name = asset_name
        self.output_dir = output_dir

    def run(self) -> None:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.log.emit(f"[net] loading Gradus source metadata for {self.asset_name}")

            request = urllib.request.Request(
                LATEST_RELEASE_URL,
                headers={"User-Agent": "m5-flasher"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)

            asset = next((item for item in payload.get("assets", []) if item.get("name") == self.asset_name), None)
            if asset is None:
                raise RuntimeError(f"Asset not found in latest upstream release: {self.asset_name}")

            release_tag = payload.get("tag_name", "latest")
            local_name = asset["name"].replace("Bruce-", "Gradus-", 1)
            destination = self.output_dir / local_name
            self.log.emit(f"[net] downloading Gradus package {release_tag} -> {destination}")
            urllib.request.urlretrieve(asset["browser_download_url"], destination)
            self.finished.emit(True, str(destination))
        except Exception as exc:  # pragma: no cover - network path
            self.finished.emit(False, str(exc))

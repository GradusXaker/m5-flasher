from __future__ import annotations

from dataclasses import dataclass

from serial.tools import list_ports


@dataclass(slots=True)
class PortInfo:
    device: str
    description: str
    hwid: str

    @property
    def label(self) -> str:
        parts = [self.device]
        if self.description and self.description != "n/a":
            parts.append(self.description)
        return " - ".join(parts)


def get_serial_ports() -> list[PortInfo]:
    ports: list[PortInfo] = []
    for port in list_ports.comports():
        ports.append(
            PortInfo(
                device=port.device,
                description=port.description or "Unknown device",
                hwid=port.hwid or "",
            )
        )
    return sorted(ports, key=lambda item: item.device)

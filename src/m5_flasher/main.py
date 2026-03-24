from __future__ import annotations

import sys

from m5_flasher.branding import create_app_icon
from m5_flasher.ui import M5FlasherWindow, create_app


def main() -> int:
    app = create_app()
    app.setWindowIcon(create_app_icon())
    window = M5FlasherWindow()
    window.setWindowIcon(create_app_icon())
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import sys

from m5_flasher.ui import M5FlasherWindow, create_app


def main() -> int:
    app = create_app()
    window = M5FlasherWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""codesnap — Offline code extractor for Ubuntu Wayland (GNOME).

Backward-compatible entrypoint. Delegates to codesnap.cli.main().
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
src_dir = root_dir / "src"

# Remove repository root from sys.path to prevent codesnap.py from shadowing src/codesnap
sys.path = [p for p in sys.path if Path(p).resolve() != root_dir]
sys.path.insert(0, str(src_dir))

if "codesnap" in sys.modules and not hasattr(sys.modules["codesnap"], "__path__"):
    del sys.modules["codesnap"]

from codesnap.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

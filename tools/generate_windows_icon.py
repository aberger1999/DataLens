"""
Generate the Windows `.ico` used by PyInstaller and Inno Setup.

Why this exists:
- The desktop/start-menu shortcut icon comes from the EXE icon resources
  (embedded at build time by PyInstaller).
- If the source logo has extra transparent padding, Windows will render the
  icon looking "tiny".

This script builds `assets/DataLens_Logo.ico` from the *cropped* logo so the
icon fills the frame at common sizes (16..256).
"""

from __future__ import annotations

import os
from pathlib import Path


SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def _repo_root() -> Path:
    # tools/ -> repo root
    return Path(__file__).resolve().parents[1]


def main() -> int:
    root = _repo_root()
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    src = assets / "DataLens_Logo_cropped.png"
    if not src.exists():
        src = assets / "DataLens_Logo.png"
    if not src.exists():
        raise FileNotFoundError(f"Logo PNG not found in {assets}")

    dst = assets / "DataLens_Logo.ico"

    from PIL import Image

    img = Image.open(src).convert("RGBA")

    # Ensure square by padding (cropped logo may be rectangular).
    w, h = img.size
    size = max(w, h)
    square = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    square.paste(img, ((size - w) // 2, (size - h) // 2))

    # Write multi-size ICO.
    square.save(dst, format="ICO", sizes=SIZES)

    print(f"Wrote: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


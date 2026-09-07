"""Generate the PWA / Android icon set from frontend/public/logo.png.

The manifest referenced /icon-192.png and /icon-512.png, but neither file
existed, so Chrome rejected the install prompt and Android had no launcher
icon. This script produces them reproducibly.

Run:  python scripts/generate_icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC = REPO_ROOT / "frontend" / "public"
SOURCE = PUBLIC / "logo.png"

# The wordmark is light (near #F0F0F0) with blue accents, so it needs a dark
# ground. #0D1117 is the label colour already used across the README badges.
BACKGROUND = (13, 17, 23, 255)

# Standard icons keep a small margin. Maskable icons must keep all meaningful
# content inside the centre 80% circle, because Android crops to the launcher's
# shape, so they get a much larger margin.
STANDARD_SIZES = (96, 192, 512)
MASKABLE_SIZE = 512
STANDARD_CONTENT_RATIO = 0.82
MASKABLE_CONTENT_RATIO = 0.58
APPLE_TOUCH_SIZE = 180


def render(size: int, content_ratio: float) -> Image.Image:
    """Centre the wordmark on a square background, scaled to content_ratio."""
    logo = Image.open(SOURCE).convert("RGBA")
    canvas = Image.new("RGBA", (size, size), BACKGROUND)

    max_edge = int(size * content_ratio)
    scale = min(max_edge / logo.width, max_edge / logo.height)
    scaled = logo.resize(
        (max(1, round(logo.width * scale)), max(1, round(logo.height * scale))),
        Image.LANCZOS,
    )

    canvas.alpha_composite(
        scaled,
        ((size - scaled.width) // 2, (size - scaled.height) // 2),
    )
    return canvas


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Source logo not found: {SOURCE}")

    written = []
    for size in STANDARD_SIZES:
        out = PUBLIC / f"icon-{size}.png"
        render(size, STANDARD_CONTENT_RATIO).save(out, "PNG", optimize=True)
        written.append(out)

    out = PUBLIC / f"icon-maskable-{MASKABLE_SIZE}.png"
    render(MASKABLE_SIZE, MASKABLE_CONTENT_RATIO).save(out, "PNG", optimize=True)
    written.append(out)

    out = PUBLIC / "apple-touch-icon.png"
    render(APPLE_TOUCH_SIZE, STANDARD_CONTENT_RATIO).save(out, "PNG", optimize=True)
    written.append(out)

    out = PUBLIC / "favicon.png"
    render(64, STANDARD_CONTENT_RATIO).save(out, "PNG", optimize=True)
    written.append(out)

    for path in written:
        print(f"{path.relative_to(REPO_ROOT)}  {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()

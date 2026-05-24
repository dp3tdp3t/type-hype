"""
Generate the type-hype app icon as PNG, ICNS (Mac), and ICO (Windows).

The design is a tiny System 1.0 window thumbnail: striped title bar
with a close box, plus a few horizontal lines representing the
passage text below. Pure B&W so it stays sharp at 16x16.

Run from the repo root:

    python3 scripts/generate_icon.py

Output (written to ./icon/ at repo root):

    icon/icon.png       — 1024x1024 reference
    icon/icon.ico       — Windows multi-size icon
    icon/icon.icns      — macOS icon (only built on macOS where
                          `iconutil` is available)
    icon/icon.iconset/  — intermediate PNGs for the macOS build
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw


ICON_DIR = Path(__file__).resolve().parents[1] / "icon"


def draw_icon(size: int) -> Image.Image:
    """Render the icon at a given square size. Pure B&W; everything
    scales proportionally so the design holds at 16x16."""
    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)

    # Outer border thickness scales with size; clamp so 16x16 still
    # has at least 1px and big sizes get a meaty frame.
    border = max(1, size // 64)
    d.rectangle([0, 0, size - 1, size - 1], outline=(0, 0, 0, 255), width=border)

    # Title bar is the top ~22% of the icon.
    bar_h = max(4, int(size * 0.22))

    # Striped pattern across the title bar — alternating 1px black
    # lines on white. At small sizes use fewer, thicker stripes.
    stripe_pitch = max(2, size // 100)  # space between lines
    stripe_thickness = max(1, size // 200)
    for y in range(border + stripe_pitch, bar_h - stripe_pitch, stripe_pitch):
        d.rectangle(
            [border, y, size - border - 1, y + stripe_thickness - 1],
            fill=(0, 0, 0, 255),
        )

    # Bottom border of the title bar.
    d.rectangle(
        [border, bar_h, size - border - 1, bar_h + border - 1],
        fill=(0, 0, 0, 255),
    )

    # Close box at the left of the title bar: small white square with
    # a black border, with the stripes "cleared" around it.
    cb_size = max(3, int(bar_h * 0.55))
    cb_margin = max(border * 2, int(bar_h * 0.18))
    cb_y0 = (bar_h - cb_size) // 2
    cb_x0 = cb_margin
    cb_x1 = cb_x0 + cb_size
    cb_y1 = cb_y0 + cb_size
    # erase stripes behind the close box first
    d.rectangle(
        [cb_x0 - border, border, cb_x1 + border, bar_h - border],
        fill=(255, 255, 255, 255),
    )
    d.rectangle([cb_x0, cb_y0, cb_x1, cb_y1],
                outline=(0, 0, 0, 255), width=max(1, border))

    # "Text lines" inside the window body — a few horizontal black
    # bars suggesting passage content. Their width and spacing scale
    # with size so they read cleanly at every resolution.
    body_top = bar_h + border * 4
    body_bottom = size - border - max(2, int(size * 0.08))
    line_thickness = max(1, size // 50)
    line_gap = line_thickness * 3
    line_indent = max(border * 2, int(size * 0.10))

    # Vary line lengths to look like paragraph text.
    relative_widths = [1.0, 0.95, 0.88, 0.97, 0.65,
                       0.92, 0.80, 0.90, 0.55]
    y = body_top
    i = 0
    while y + line_thickness <= body_bottom and i < len(relative_widths):
        w = relative_widths[i]
        x0 = line_indent
        x1 = int(x0 + (size - 2 * line_indent) * w)
        d.rectangle([x0, y, x1, y + line_thickness - 1], fill=(0, 0, 0, 255))
        y += line_thickness + line_gap
        i += 1

    return img


def main():
    ICON_DIR.mkdir(parents=True, exist_ok=True)

    # 1024x1024 reference PNG.
    big = draw_icon(1024)
    big.save(ICON_DIR / "icon.png")
    print(f"Wrote {ICON_DIR / 'icon.png'}")

    # Windows multi-size ICO.
    ico_sizes = [16, 32, 48, 64, 128, 256]
    ico_imgs = [draw_icon(s) for s in ico_sizes]
    ico_imgs[0].save(
        ICON_DIR / "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in ico_sizes],
        append_images=ico_imgs[1:],
    )
    print(f"Wrote {ICON_DIR / 'icon.ico'}")

    # macOS iconset → iconutil → icns. Only works on macOS where
    # `iconutil` ships with the system. On other platforms we leave
    # the iconset folder around for use elsewhere.
    iconset = ICON_DIR / "icon.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()
    sizes = [16, 32, 128, 256, 512]
    for s in sizes:
        draw_icon(s).save(iconset / f"icon_{s}x{s}.png")
        draw_icon(s * 2).save(iconset / f"icon_{s}x{s}@2x.png")
    print(f"Wrote {iconset}/*.png")

    if sys.platform == "darwin":
        try:
            subprocess.run(
                ["iconutil", "-c", "icns",
                 "-o", str(ICON_DIR / "icon.icns"), str(iconset)],
                check=True,
            )
            print(f"Wrote {ICON_DIR / 'icon.icns'}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"iconutil failed: {e}")
    else:
        print("Skipping .icns build (only works on macOS)")


if __name__ == "__main__":
    main()

"""Build the Windows and archive icons from the polished raster master."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "crow_pack.png"
OUTPUT = ROOT / "assets" / "crow_pack.ico"


def main() -> None:
    with Image.open(SOURCE) as image:
        rgba = image.convert("RGBA")
        rgba.save(
            OUTPUT,
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
        from PIL import ImageDraw, ImageFont
        font = ImageFont.truetype("arialbd.ttf", 230)
        for label in ("ZIP", "7Z", "RAR", "TAR", "ISO", "CBZ"):
            variant = rgba.copy()
            draw = ImageDraw.Draw(variant)
            draw.rounded_rectangle((32, 700, 992, 1000), radius=75, fill="#59D8EC")
            draw.text((512, 850), label, font=font, fill="#080C12", anchor="mm")
            variant.save(ROOT / "assets" / (label.lower() + ".ico"), format="ICO",
                         sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    print(OUTPUT)


if __name__ == "__main__":
    main()

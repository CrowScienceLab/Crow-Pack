"""Render the checked-in Crow Pack SVG into a multi-resolution Windows ICO."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "crow_pack.svg"
OUTPUT = ROOT / "assets" / "crow_pack.ico"


def main() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    renderer = QSvgRenderer(str(SOURCE))
    if not renderer.isValid():
        raise RuntimeError(f"Invalid SVG: {SOURCE}")

    canvas = QImage(256, 256, QImage.Format_ARGB32)
    canvas.fill(0)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    renderer.render(painter, QRectF(0, 0, 256, 256))
    painter.end()

    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    if not canvas.save(buffer, "PNG"):
        raise RuntimeError("Could not render icon PNG")
    buffer.close()

    with Image.open(io.BytesIO(bytes(data))) as image:
        rgba = image.convert("RGBA")
        rgba.save(
            OUTPUT,
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
    print(OUTPUT)
    del app


if __name__ == "__main__":
    main()

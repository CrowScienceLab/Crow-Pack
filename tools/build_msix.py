"""Build the Microsoft Store MSIX package from the PyInstaller output."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.5.3"
PACKAGE_DIR = ROOT / "build" / "msix" / "CrowPack"
OUTPUT = ROOT / "release" / f"CrowPack-v{VERSION}-Store-x64.msix"


def _find_makeappx(explicit: str | None) -> Path:
    candidates = []
    for value in (explicit, os.environ.get("MAKEAPPX")):
        if value:
            candidates.append(Path(value))
    for base in (
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Windows Kits" / "10" / "bin",
        ROOT / ".tools" / "windows-sdk",
    ):
        if base.is_dir():
            candidates.extend(sorted(base.rglob("makeappx.exe"), reverse=True))
    for candidate in candidates:
        if candidate.is_file() and "x64" in {part.lower() for part in candidate.parts}:
            return candidate
    raise FileNotFoundError("makeappx.exe를 찾을 수 없습니다. --makeappx 경로를 지정하세요.")


def _asset(source: Image.Image, width: int, height: int, destination: Path) -> None:
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    margin = max(2, round(min(width, height) * 0.08))
    icon = source.copy()
    icon.thumbnail((width - margin * 2, height - margin * 2), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, ((width - icon.width) // 2, (height - icon.height) // 2))
    canvas.save(destination, "PNG", optimize=True)


def build(makeappx: Path) -> Path:
    app_dir = ROOT / "dist" / "CrowPack"
    if not (app_dir / "CrowPack.exe").is_file():
        raise FileNotFoundError("dist/CrowPack/CrowPack.exe가 없습니다. build_exe.bat을 먼저 실행하세요.")
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    shutil.copytree(app_dir, PACKAGE_DIR)
    shutil.copy2(ROOT / "store" / "AppxManifest.xml", PACKAGE_DIR / "AppxManifest.xml")
    asset_dir = PACKAGE_DIR / "StoreAssets"
    asset_dir.mkdir()
    with Image.open(ROOT / "assets" / "crow_pack.png") as opened:
        source = opened.convert("RGBA")
        for name, width, height in (
            ("StoreLogo.png", 50, 50),
            ("Square44x44Logo.png", 44, 44),
            ("Square150x150Logo.png", 150, 150),
            ("Square310x310Logo.png", 310, 310),
            ("Wide310x150Logo.png", 310, 150),
        ):
            _asset(source, width, height, asset_dir / name)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.unlink(missing_ok=True)
    subprocess.run(
        [str(makeappx), "pack", "/v", "/h", "SHA256", "/d", str(PACKAGE_DIR), "/p", str(OUTPUT)],
        check=True,
        cwd=ROOT,
    )
    return OUTPUT


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--makeappx", help="Windows SDK makeappx.exe path")
    args = parser.parse_args()
    output = build(_find_makeappx(args.makeappx))
    print(f"{output}: {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()

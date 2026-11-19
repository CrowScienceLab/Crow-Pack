"""Build the Microsoft Store MSIX package from the PyInstaller output."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.7"
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
    icon = ImageOps.contain(source, (width, height), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, ((width - icon.width) // 2, (height - icon.height) // 2))
    canvas.save(destination, "PNG", optimize=True)


def generate_assets(source: Image.Image, asset_dir: Path) -> None:
    """Full-size shell art, separate exact-size and DPI-qualified resources."""
    for name, width, height in (
        ('StoreLogo', 50, 50), ('Square44x44Logo', 44, 44),
        ('Square150x150Logo', 150, 150), ('Square310x310Logo', 310, 310),
        ('Wide310x150Logo', 310, 150),
    ):
        _asset(source, width, height, asset_dir / f'{name}.png')
        for scale in (100, 125, 150, 200, 250, 300, 400):
            _asset(source, round(width * scale / 100), round(height * scale / 100),
                   asset_dir / f'{name}.scale-{scale}.png')
    for size in (16, 20, 24, 30, 32, 36, 40, 48, 60, 64, 72, 80, 96, 128, 256):
        for variant in ('', '_altform-unplated', '_altform-lightunplated'):
            _asset(source, size, size, asset_dir / f'Square44x44Logo.targetsize-{size}{variant}.png')


def build(makeappx: Path) -> Path:
    app_dir = ROOT / "dist" / "CrowPack"
    if not (app_dir / "CrowPack.exe").is_file():
        raise FileNotFoundError("dist/CrowPack/CrowPack.exe가 없습니다. build_exe.bat을 먼저 실행하세요.")
    if PACKAGE_DIR.exists():
        if PACKAGE_DIR.resolve() != PACKAGE_DIR or not PACKAGE_DIR.is_relative_to(ROOT / 'build'):
            raise ValueError('MSIX 임시 폴더가 빌드 경로 밖을 가리킵니다.')
        shutil.rmtree(PACKAGE_DIR)
    shutil.copytree(app_dir, PACKAGE_DIR)
    shutil.copy2(ROOT / "store" / "AppxManifest.xml", PACKAGE_DIR / "AppxManifest.xml")
    asset_dir = PACKAGE_DIR / "StoreAssets"
    asset_dir.mkdir()
    with Image.open(ROOT / "assets" / "CrowPack.png") as opened:
        source = opened.convert("RGBA")
        generate_assets(source, asset_dir)
    makepri = makeappx.with_name('makepri.exe')
    if not makepri.is_file():
        raise FileNotFoundError('makepri.exe가 필요합니다. Windows SDK Build Tools를 확인하세요.')
    (ROOT / 'tmp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='crowpack-pri-', dir=ROOT / 'tmp') as resource_root:
        # Keep StoreAssets in the logical URI. Indexing that directory directly
        # strips its prefix and prevents the manifest from resolving variants.
        shutil.copytree(asset_dir, Path(resource_root) / 'StoreAssets')
        subprocess.run([str(makepri), 'new', '/pr', resource_root,
                        '/cf', str(ROOT / 'store/priconfig.xml'),
                        '/mn', str(PACKAGE_DIR / 'AppxManifest.xml'),
                        '/of', str(PACKAGE_DIR / 'resources.pri'), '/o'], check=True, cwd=ROOT)
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

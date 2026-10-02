"""Produce the versioned installer, portable, source, and checksum release artifacts."""
import hashlib
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.5.3'
OUTPUT = ROOT / 'release'


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    installer = OUTPUT / f'CrowPack-v{VERSION}-Setup-x64.exe'
    if not installer.is_file():
        raise FileNotFoundError(installer)
    portable = OUTPUT / f'CrowPack-v{VERSION}-Portable-x64.zip'
    with zipfile.ZipFile(portable, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted((ROOT / 'dist/CrowPack').rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT / 'dist'))
    files = subprocess.check_output(
        [
            'git',
            '-c',
            f'safe.directory={ROOT.as_posix()}',
            'ls-files',
            '-z',
            '--cached',
            '--others',
            '--exclude-standard',
        ],
        cwd=ROOT,
    ).decode('utf-8').split('\0')
    with zipfile.ZipFile(OUTPUT / f'CrowPack-v{VERSION}-Source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(set(files)):
            if name and name != 'release/SHA256SUMS.txt' and (ROOT / name).is_file():
                archive.write(ROOT / name, 'Crow-Pack/' + name)
    rows = []
    for path in sorted(OUTPUT.glob(f'CrowPack-v{VERSION}-*')):
        if path.suffix.lower() in {'.exe', '.msix', '.zip'}:
            with path.open('rb') as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
            rows.append(f'{digest}  {path.name}\n')
    (OUTPUT / 'SHA256SUMS.txt').write_text(''.join(rows), encoding='utf-8')
    print(OUTPUT)
    for path in sorted(OUTPUT.iterdir()):
        print(f'{path.name}: {path.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()

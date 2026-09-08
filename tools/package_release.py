"""Produce local review artifacts only. Does not upload or change Git history."""
import hashlib
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT.parent / 'outputs' / 'Crow-Pack-v1.5.0'


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    installer = ROOT / 'release/CrowPack-v1.5.0-Setup-x64.exe'
    shutil.copy2(installer, OUTPUT / installer.name)
    portable = OUTPUT / 'CrowPack-v1.5.0-Portable-x64.zip'
    with zipfile.ZipFile(portable, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted((ROOT / 'dist/CrowPack').rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT / 'dist'))
    files = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).decode('utf-8').split('\0')
    with zipfile.ZipFile(OUTPUT / 'CrowPack-v1.5.0-Source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(set(files)):
            if name and (ROOT / name).is_file():
                archive.write(ROOT / name, 'Crow-Pack/' + name)
    shutil.copy2(ROOT / 'docs/V1.5-VALIDATION.md', OUTPUT / 'VALIDATION.md')
    rows = []
    for path in sorted(OUTPUT.iterdir()):
        if path.suffix in {'.exe', '.zip'}:
            with path.open('rb') as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
            rows.append(f'{digest}  {path.name}\n')
    (OUTPUT / 'SHA256SUMS.txt').write_text(''.join(rows), encoding='utf-8')
    print(OUTPUT)
    for path in sorted(OUTPUT.iterdir()):
        print(f'{path.name}: {path.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()

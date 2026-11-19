"""Produce the versioned installer, portable, source, and checksum release artifacts."""
import argparse
import hashlib
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.7'
OUTPUT = ROOT / 'release'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include', action='append', default=[], metavar='PATH',
                        help='Include an explicitly reviewed untracked source file (repeatable).')
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    installer = OUTPUT / f'CrowPack-v{VERSION}-Setup-x64.exe'
    msix = OUTPUT / f'CrowPack-v{VERSION}-Store-x64.msix'
    dist = ROOT / 'dist' / 'CrowPack'
    for required in (installer, msix, dist / 'CrowPack.exe'):
        if not required.is_file():
            raise FileNotFoundError(required)
    files = subprocess.check_output(
        [
            'git',
            '-c',
            f'safe.directory={ROOT.as_posix()}',
            'ls-files',
            '-z',
            '--cached',
        ],
        cwd=ROOT,
    ).decode('utf-8').split('\0')
    source_files = {}
    for name in sorted(set(files + args.include) - {'', 'release/SHA256SUMS.txt'}):
        relative = Path(name)
        path = ROOT / relative
        if relative.anchor or '..' in relative.parts or path.resolve() != path:
            raise ValueError(f'Unsafe source archive path: {name}')
        if path.is_file():
            source_files[relative.as_posix()] = path
        elif name in args.include:
            raise FileNotFoundError(path)
    portable = OUTPUT / f'CrowPack-v{VERSION}-Portable-x64.zip'
    with zipfile.ZipFile(portable, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(dist.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(dist.parent))
    with zipfile.ZipFile(OUTPUT / f'CrowPack-v{VERSION}-Source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, path in source_files.items():
            archive.write(path, 'Crow-Pack/' + name)
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

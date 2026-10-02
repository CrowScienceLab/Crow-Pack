"""Generate the offline UI icon module from the pinned Lucide SVG distribution."""

import argparse
import json
import re
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = {
    'folder': 'folder', 'file': 'file', 'openArchive': 'folder-open',
    'newArchive': 'package-plus', 'extractHere': 'download',
    'extractCustom': 'folder-down', 'isoDisc': 'disc-3',
    'pdfOptimize': 'file-down', 'update': 'refresh-cw', 'association': 'link',
    'addFile': 'file-plus-2', 'delete': 'trash-2', 'test': 'shield-check',
    'codepage': 'languages', 'cancel': 'x', 'info': 'circle-help',
    'settings': 'settings-2', 'tools': 'wrench', 'convert': 'arrow-right-left',
    'batch': 'files', 'cbz': 'book-image', 'privacy': 'file-lock-2',
    'split': 'split',
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    icons = {'logo': '<img src="../../assets/crow_pack.png" alt="" class="crow-brand-image">'}
    with tarfile.open(args.archive) as archive:
        package = json.loads(archive.extractfile('package/package.json').read())
        if package['version'] != '0.468.0':
            raise ValueError('Expected Lucide 0.468.0')
        for key, name in ICONS.items():
            svg = archive.extractfile(f'package/icons/{name}.svg').read().decode()
            svg = re.sub(r'<!--.*?-->', '', svg, flags=re.S).strip()
            svg = re.sub(r'class="[^"]*"', 'class="crow-svg-icon"', svg)
            svg = svg.replace('<svg ', '<svg aria-hidden="true" focusable="false" ')
            icons[key] = svg
        license_text = archive.extractfile('package/LICENSE').read().decode()
    (ROOT / 'assets' / 'LUCIDE-LICENSE.txt').write_text(license_text, encoding='utf-8')
    (ROOT / 'src/ui/icons.js').write_text(
        '/* Lucide 0.468.0 — ISC / MIT. See assets/LUCIDE-LICENSE.txt. */\n'
        + 'const CrowIcons = ' + json.dumps(icons, ensure_ascii=False, indent=2) + ';\n'
        + 'CrowIcons.extract = CrowIcons.extractHere;\nwindow.CrowIcons = CrowIcons;\n',
        encoding='utf-8',
    )


if __name__ == '__main__':
    main()

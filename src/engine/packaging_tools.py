"""Safe, reusable v1.5 packaging operations; no GUI or stored passwords."""

import hashlib
import hmac
import os
import re
import shutil
import tempfile
import time
import uuid
import zipfile
from pathlib import Path

from .archive_manager import ArchiveManager
from .archive_safety import iter_source_files, member_is_selected, safe_destination, validate_entries

FORMATS = {"ZIP": ".zip", "7Z": ".7z", "TAR": ".tar", "TAR.GZ": ".tar.gz", "TAR.BZ2": ".tar.bz2", "TAR.XZ": ".tar.xz"}
IMAGES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


def sha256(path, progress=None):
    digest = hashlib.sha256()
    total = os.path.getsize(path)
    done = 0
    with open(path, "rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            done += len(chunk)
            if progress:
                progress(done, total, os.path.basename(path))
    return digest.hexdigest()


def verify_checksum(path, expected):
    expected = expected.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("SHA-256 값은 64자리 16진수여야 합니다.")
    actual = sha256(path)
    return {"path": path, "sha256": actual, "matches": hmac.compare_digest(actual, expected)}


def checksum_manifest(paths, output, progress=None):
    rows = []
    for path in paths:
        name = os.path.relpath(path, os.path.dirname(os.path.abspath(output))).replace("\\", "/")
        if any(c in name for c in "\r\n"):
            raise ValueError("체크섬 파일에는 줄바꿈이 포함된 파일명을 사용할 수 없습니다.")
        rows.append(f"{sha256(path, progress)}  {name}\n")
    with open(output, "x", encoding="utf-8", newline="\n") as target:
        target.writelines(rows)
    return output


def create_cbz(paths, output, renumber=True, progress=None):
    targets = [(p, n) for p, n in iter_source_files(paths, output) if Path(p).suffix.lower() in IMAGES]
    targets.sort(key=lambda pair: [int(s) if s.isdigit() else s.casefold() for s in re.split(r"(\d+)", pair[1])])
    if not targets:
        raise ValueError("지원되는 이미지 파일이 없습니다.")
    names = [
        f"{i:0{max(3, len(str(len(targets))))}d}{Path(p).suffix.lower()}" if renumber else n.replace("\\", "/")
        for i, (p, n) in enumerate(targets, 1)
    ]
    validate_entries([{"name": n, "size": os.path.getsize(p)} for (p, _), n in zip(targets, names)])
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for index, ((path, _), name) in enumerate(zip(targets, names), 1):
            archive.write(path, name)
            if progress:
                progress(index, len(targets), name)
    return output


def convert_archive(source, output, fmt, password=None, output_password=None, progress=None):
    if fmt not in FORMATS:
        raise ValueError("지원하지 않는 출력 형식입니다.")
    if os.path.exists(output):
        raise FileExistsError("출력 파일이 이미 존재합니다.")
    if not output.lower().endswith(FORMATS[fmt]):
        raise ValueError("출력 확장자가 선택한 형식과 일치하지 않습니다.")
    with tempfile.TemporaryDirectory(prefix="crowpack-convert-") as scratch:
        extracted = os.path.join(scratch, "content")
        ArchiveManager.extract_archive(source, extracted, "current", password=password, progress_callback=progress)
        sources = [str(p) for p in Path(extracted).iterdir()]
        staged = os.path.join(scratch, "converted" + FORMATS[fmt])
        ArchiveManager.create_archive(sources, staged, fmt, password=output_password, progress_callback=progress)
        valid, error = ArchiveManager.test_archive(staged, output_password)
        if not valid:
            raise ValueError(error or "변환 결과 무결성 검사 실패")
        # Extracting again checks payloads for TAR too, not just its headers.
        ArchiveManager.extract_archive(staged, os.path.join(scratch, "verify"), "current", password=output_password)
        with open(staged, "rb") as src, open(output, "xb") as dest:
            shutil.copyfileobj(src, dest, 1024 * 1024)
    return output


def batch_extract(paths, destination, mode="new_folder", password=None, progress=None):
    if mode not in {"new_folder", "smart", "current"}:
        raise ValueError("잘못된 해제 옵션입니다.")
    results = []
    for index, source in enumerate(paths, 1):
        try:
            if progress:
                progress(index, len(paths), os.path.basename(source))
            base = Path(source).stem
            if base.lower().endswith(".tar"):
                base = base[:-4]
            target = os.path.abspath(destination)
            info = ArchiveManager.list_archive(source, password=password)
            validate_entries(info["items"])
            if mode == "new_folder" or (mode == "smart" and not info["is_single_root"]):
                target = safe_destination(target, base)
                candidate = target
                number = 2
                while os.path.exists(candidate):
                    candidate = f"{target} ({number})"
                    number += 1
                target = candidate
            for entry in info["items"]:
                candidate = safe_destination(target, entry["name"])
                if os.path.exists(candidate) and not entry.get("is_dir"):
                    raise FileExistsError(f"기존 파일 충돌: {entry['name']}")
            ArchiveManager.extract_archive(source, target, "current", password=password)
            results.append({"path": source, "success": True, "output_dir": target})
        except Exception as exc:
            results.append({"path": source, "success": False, "error": str(exc)})
    return results


class DragExportManager:
    """Retain session files for Explorer copying, only clean our UUID directories."""

    def __init__(self, root=None):
        self.root = Path(root or Path(tempfile.gettempdir()) / "CrowPack" / "drag")
        self.root.mkdir(parents=True, exist_ok=True)
        self.cleanup_old()
        self.session = self.root / str(uuid.uuid4())
        self.session.mkdir()

    def cleanup_old(self, max_age=7 * 86400):
        for path in self.root.iterdir():
            try:
                uuid.UUID(path.name)
                if path.is_dir() and not path.is_symlink() and time.time() - path.stat().st_mtime > max_age:
                    shutil.rmtree(path)
            except (ValueError, OSError):
                continue

    def prepare(self, source, selected, password=None):
        if not selected:
            raise ValueError("추출할 항목을 선택하세요.")
        info = ArchiveManager.list_archive(source, password=password)
        validate_entries(info["items"])
        chosen = [e for e in info["items"] if member_is_selected(e["name"], selected)]
        if not chosen:
            raise ValueError("선택 항목을 찾을 수 없습니다.")
        target = self.session / str(uuid.uuid4())
        ArchiveManager.extract_archive(source, str(target), "current", selected, password)
        # Some legacy handlers extract all members: export only explicitly selected roots.
        roots = []
        for entry in sorted(chosen, key=lambda e: len(e["name"])):
            path = Path(safe_destination(str(target), entry["name"]))
            if path.exists() and not any(path == p or p in path.parents for p in roots):
                roots.append(path)
        return [str(p) for p in roots]

    def close(self):
        # Keep very recent drags alive even if the app closes during an Explorer copy.
        self.cleanup_old()

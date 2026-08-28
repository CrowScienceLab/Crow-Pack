"""Shared safety checks for untrusted archive content."""

from __future__ import annotations

import ntpath
import os
import stat
import tempfile
import unicodedata
from dataclasses import dataclass
from typing import BinaryIO, Iterable, Mapping


class ArchiveSecurityError(ValueError):
    """Raised when an archive violates Crow Pack's extraction policy."""


@dataclass(frozen=True)
class ExtractionPolicy:
    max_entries: int = 100_000
    max_total_size: int = 32 * 1024**3
    max_file_size: int = 8 * 1024**3
    max_compression_ratio: int = 1_000
    max_member_name_length: int = 1_024


DEFAULT_POLICY = ExtractionPolicy()

_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def normalize_member_name(name: str, policy: ExtractionPolicy = DEFAULT_POLICY) -> str:
    """Return a portable relative member name, or reject an unsafe one."""
    if not isinstance(name, str) or not name:
        raise ArchiveSecurityError("아카이브 항목 이름이 비어 있습니다.")
    if "\x00" in name:
        raise ArchiveSecurityError("아카이브 항목 이름에 NUL 문자가 있습니다.")

    normalized = unicodedata.normalize("NFC", name).replace("\\", "/")
    if len(normalized) > policy.max_member_name_length:
        raise ArchiveSecurityError("아카이브 항목 이름이 너무 깁니다.")
    if normalized.startswith("/") or ntpath.splitdrive(normalized)[0]:
        raise ArchiveSecurityError(f"절대 경로 항목을 차단했습니다: {name}")

    parts = []
    for part in normalized.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise ArchiveSecurityError(f"상위 경로 이동 항목을 차단했습니다: {name}")
        if part.rstrip(" .") != part:
            raise ArchiveSecurityError(f"Windows에서 모호한 경로를 차단했습니다: {name}")
        if part.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES:
            raise ArchiveSecurityError(f"Windows 예약 파일명을 차단했습니다: {name}")
        parts.append(part)

    if not parts:
        raise ArchiveSecurityError(f"유효하지 않은 아카이브 항목입니다: {name}")
    return "/".join(parts)


def safe_destination(root: str, member_name: str) -> str:
    """Resolve a member below root, including existing symlink/junction checks."""
    safe_name = normalize_member_name(member_name)
    root_real = os.path.realpath(os.path.abspath(root))
    destination = os.path.realpath(os.path.join(root_real, *safe_name.split("/")))
    try:
        inside = os.path.commonpath((root_real, destination)) == root_real
    except ValueError:
        inside = False
    if not inside:
        raise ArchiveSecurityError(f"대상 폴더 밖으로 나가는 경로를 차단했습니다: {member_name}")
    if os.path.lexists(destination) and os.path.islink(destination):
        raise ArchiveSecurityError(f"심볼릭 링크 대상 덮어쓰기를 차단했습니다: {member_name}")
    return destination


def member_is_selected(member_name: str, selected_files: Iterable[str] | None) -> bool:
    """Match a selected file or every descendant of a selected directory."""
    if selected_files is None:
        return True
    normalized = member_name.replace("\\", "/").rstrip("/")
    for selected in selected_files:
        choice = str(selected).replace("\\", "/").rstrip("/")
        if normalized == choice or normalized.startswith(f"{choice}/"):
            return True
    return False


def validate_entries(
    entries: Iterable[Mapping[str, object]],
    policy: ExtractionPolicy = DEFAULT_POLICY,
) -> None:
    """Reject oversized, duplicated, linked, or suspicious archive entries."""
    seen: set[str] = set()
    total_size = 0
    count = 0

    for entry in entries:
        name = normalize_member_name(str(entry.get("name", "")), policy)
        folded = name.casefold()
        if folded in seen:
            raise ArchiveSecurityError(f"중복되거나 대소문자 충돌이 있는 항목입니다: {name}")
        seen.add(folded)
        count += 1
        if count > policy.max_entries:
            raise ArchiveSecurityError(f"아카이브 항목 수가 제한({policy.max_entries:,}개)을 초과합니다.")
        if bool(entry.get("is_link", False)):
            raise ArchiveSecurityError(f"링크 항목은 안전을 위해 해제하지 않습니다: {name}")

        size = max(0, int(entry.get("size", 0) or 0))
        compressed = max(0, int(entry.get("compressed_size", 0) or 0))
        if size > policy.max_file_size:
            raise ArchiveSecurityError(f"단일 파일 크기 제한을 초과합니다: {name}")
        total_size += size
        if total_size > policy.max_total_size:
            raise ArchiveSecurityError("전체 해제 크기 제한(32 GiB)을 초과합니다.")
        if size >= 100 * 1024**2 and compressed and size / compressed > policy.max_compression_ratio:
            raise ArchiveSecurityError(f"비정상적으로 높은 압축률을 감지했습니다: {name}")


def copy_stream_limited(
    source: BinaryIO,
    destination: str,
    expected_size: int | None = None,
    policy: ExtractionPolicy = DEFAULT_POLICY,
) -> int:
    """Copy one member atomically while enforcing the single-file limit."""
    parent = os.path.dirname(destination)
    os.makedirs(parent, exist_ok=True)
    temp_path = ""
    written = 0
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=parent, prefix=".crowpack-", delete=False) as target:
            temp_path = target.name
            while chunk := source.read(1024 * 1024):
                written += len(chunk)
                if written > policy.max_file_size:
                    raise ArchiveSecurityError("해제 중 단일 파일 크기 제한을 초과했습니다.")
                target.write(chunk)
        if expected_size is not None and written != expected_size:
            raise ArchiveSecurityError(
                f"아카이브 헤더 크기와 실제 해제 크기가 다릅니다 ({expected_size:,} != {written:,})."
            )
        os.replace(temp_path, destination)
        temp_path = ""
        return written
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def iter_source_files(paths: Iterable[str], output_path: str | None = None):
    """Yield regular source files without following links or including output."""
    output_real = os.path.realpath(output_path) if output_path else None
    seen: set[str] = set()
    for path in paths:
        absolute = os.path.abspath(path)
        if os.path.islink(absolute):
            raise ArchiveSecurityError(f"링크 원본은 압축하지 않습니다: {path}")
        if os.path.isdir(absolute):
            base_dir = os.path.dirname(absolute)
            for root, dirs, files in os.walk(absolute, followlinks=False):
                linked_dirs = [name for name in dirs if os.path.islink(os.path.join(root, name))]
                if linked_dirs:
                    raise ArchiveSecurityError(f"링크 폴더는 압축하지 않습니다: {os.path.join(root, linked_dirs[0])}")
                for filename in files:
                    full_path = os.path.join(root, filename)
                    if os.path.islink(full_path):
                        raise ArchiveSecurityError(f"링크 파일은 압축하지 않습니다: {full_path}")
                    real_path = os.path.realpath(full_path)
                    if output_real and real_path == output_real:
                        continue
                    if real_path not in seen and stat.S_ISREG(os.stat(real_path).st_mode):
                        seen.add(real_path)
                        yield real_path, os.path.relpath(real_path, base_dir)
        elif os.path.isfile(absolute):
            real_path = os.path.realpath(absolute)
            if output_real and real_path == output_real:
                raise ArchiveSecurityError("출력 파일을 입력 파일로 동시에 사용할 수 없습니다.")
            if real_path not in seen:
                seen.add(real_path)
                yield real_path, os.path.basename(absolute)
        else:
            raise FileNotFoundError(f"압축할 경로를 찾을 수 없습니다: {path}")

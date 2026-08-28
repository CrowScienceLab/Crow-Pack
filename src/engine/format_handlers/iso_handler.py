"""Safe ISO 9660/Joliet/Rock Ridge image creation and extraction."""

from __future__ import annotations

import os
import re
import tempfile
import unicodedata
from typing import Any, Dict, List, Optional

import pycdlib

from ..archive_safety import (
    DEFAULT_POLICY,
    ArchiveSecurityError,
    copy_stream_limited,
    normalize_member_name,
    safe_destination,
    validate_entries,
)
from ..encoding_helper import normalize_korean_text


class IsoHandler:
    """Create, list, and safely copy files from data-disc images."""

    MAX_ISO9660_FILE_SIZE = 4 * 1024**3 - 1

    @staticmethod
    def _volume_identifier(label: str) -> str:
        normalized = unicodedata.normalize("NFKD", label or "CROW_PACK")
        ascii_label = normalized.encode("ascii", "ignore").decode("ascii").upper()
        cleaned = re.sub(r"[^A-Z0-9_]", "_", ascii_label).strip("_")
        return (cleaned or "CROW_PACK")[:32]

    @staticmethod
    def _unique_root_name(name: str, used: set[str]) -> str:
        safe = normalize_member_name(name).split("/")[-1]
        candidate = safe
        stem, extension = os.path.splitext(safe)
        index = 2
        while candidate.casefold() in used:
            candidate = f"{stem}_{index}{extension}"
            index += 1
        used.add(candidate.casefold())
        return candidate

    @classmethod
    def _collect_creation_entries(cls, source_paths: List[str], output_path: str):
        if not source_paths:
            raise ValueError("ISO에 넣을 파일이나 폴더가 없습니다.")

        output_real = os.path.realpath(output_path)
        used_roots: set[str] = set()
        directories: set[str] = set()
        files = []
        total_size = 0

        for source in source_paths:
            absolute = os.path.abspath(source)
            if not os.path.exists(absolute):
                raise FileNotFoundError(f"ISO에 넣을 경로를 찾을 수 없습니다: {source}")
            if os.path.islink(absolute):
                raise ArchiveSecurityError(f"링크 원본은 ISO에 넣지 않습니다: {source}")

            root_name = cls._unique_root_name(os.path.basename(absolute.rstrip("\\/")), used_roots)
            if os.path.isdir(absolute):
                directories.add(root_name)
                for current_root, child_dirs, child_files in os.walk(absolute, followlinks=False):
                    for child in child_dirs:
                        child_path = os.path.join(current_root, child)
                        if os.path.islink(child_path):
                            raise ArchiveSecurityError(f"링크 폴더는 ISO에 넣지 않습니다: {child_path}")
                        inside = os.path.relpath(child_path, absolute).replace("\\", "/")
                        relative = f"{root_name}/{inside}"
                        directories.add(normalize_member_name(relative))
                    for child in child_files:
                        child_path = os.path.join(current_root, child)
                        if os.path.islink(child_path):
                            raise ArchiveSecurityError(f"링크 파일은 ISO에 넣지 않습니다: {child_path}")
                        if os.path.realpath(child_path) == output_real:
                            continue
                        inside = os.path.relpath(child_path, absolute).replace("\\", "/")
                        relative = normalize_member_name(f"{root_name}/{inside}")
                        size = os.path.getsize(child_path)
                        files.append((child_path, relative, size))
                        total_size += size
            else:
                if os.path.realpath(absolute) == output_real:
                    raise ArchiveSecurityError("출력 ISO를 입력 파일로 동시에 사용할 수 없습니다.")
                size = os.path.getsize(absolute)
                files.append((absolute, root_name, size))
                total_size += size

        if len(files) + len(directories) > DEFAULT_POLICY.max_entries:
            raise ArchiveSecurityError("ISO 항목 수가 안전 제한을 초과합니다.")
        if total_size > DEFAULT_POLICY.max_total_size:
            raise ArchiveSecurityError("ISO 원본 파일의 총 크기가 32 GiB 제한을 초과합니다.")
        oversized = next((logical for _, logical, size in files if size > cls.MAX_ISO9660_FILE_SIZE), None)
        if oversized:
            raise ArchiveSecurityError(f"4 GiB 이상 파일은 현재 데이터 ISO 생성에서 지원하지 않습니다: {oversized}")

        return sorted(directories, key=lambda value: (value.count("/"), value.casefold())), files

    @classmethod
    def create(
        cls,
        source_paths: List[str],
        output_path: str,
        volume_label: str = "CROW_PACK",
        progress_callback=None,
    ) -> str:
        """Create a portable data ISO with Joliet and Rock Ridge names."""
        destination = os.path.abspath(output_path)
        if not destination.lower().endswith(".iso"):
            destination += ".iso"
        if os.path.exists(destination):
            raise FileExistsError("기존 파일 보호를 위해 출력 ISO를 덮어쓰지 않았습니다.")
        output_dir = os.path.dirname(destination)
        os.makedirs(output_dir, exist_ok=True)

        directories, files = cls._collect_creation_entries(source_paths, destination)
        iso = pycdlib.PyCdlib()
        temp_path = ""
        directory_aliases = {"": ""}
        try:
            iso.new(
                interchange_level=3,
                joliet=3,
                rock_ridge="1.09",
                vol_ident=cls._volume_identifier(volume_label),
            )
            for index, logical in enumerate(directories, start=1):
                parent = logical.rsplit("/", 1)[0] if "/" in logical else ""
                alias = f"D{index:07d}"
                iso_parent = directory_aliases[parent]
                iso_path = f"{iso_parent}/{alias}" if iso_parent else f"/{alias}"
                directory_aliases[logical] = iso_path
                iso.add_directory(
                    iso_path=iso_path,
                    rr_name=logical.rsplit("/", 1)[-1],
                    joliet_path=f"/{logical}",
                )

            total = len(files)
            for index, (source, logical, _) in enumerate(files, start=1):
                parent = logical.rsplit("/", 1)[0] if "/" in logical else ""
                extension = os.path.splitext(logical)[1].lstrip(".").upper()
                extension = re.sub(r"[^A-Z0-9_]", "", extension)[:3] or "DAT"
                alias = f"F{index:07d}.{extension};1"
                iso_parent = directory_aliases.get(parent, "")
                iso_path = f"{iso_parent}/{alias}" if iso_parent else f"/{alias}"
                iso.add_file(
                    source,
                    iso_path=iso_path,
                    rr_name=logical.rsplit("/", 1)[-1],
                    joliet_path=f"/{logical}",
                )
                if progress_callback:
                    progress_callback(index, total, logical)

            with tempfile.NamedTemporaryFile(
                suffix=".iso",
                prefix=".crowpack-iso-",
                dir=output_dir,
                delete=False,
            ) as temp_file:
                temp_path = temp_file.name
            iso.write(temp_path)
            iso.close()

            verification = cls.list_contents(temp_path)
            if sum(1 for entry in verification if not entry["is_dir"]) != len(files):
                raise ValueError("생성된 ISO의 파일 수 검증에 실패했습니다.")
            os.replace(temp_path, destination)
            temp_path = ""
            return destination
        finally:
            try:
                iso.close()
            except Exception:
                pass
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    @staticmethod
    def _path_mode(iso: pycdlib.PyCdlib) -> str:
        # Prefer the richest namespace, matching pycdlib's official extractor.
        if iso.has_udf():
            return "udf_path"
        if iso.has_rock_ridge():
            return "rr_path"
        if iso.has_joliet():
            return "joliet_path"
        return "iso_path"

    @staticmethod
    def _join_iso_path(directory: str, name: str) -> str:
        if directory == "/":
            return f"/{name}"
        return f"{directory.rstrip('/')}/{name}"

    @staticmethod
    def _display_path(source_path: str, path_mode: str, is_dir: bool = False) -> str:
        parts = []
        for part in source_path.replace("\\", "/").split("/"):
            if not part:
                continue
            if path_mode == "iso_path":
                part = re.sub(r";\d+$", "", part)
                part = part.rstrip(".")
            parts.append(part)
        display = normalize_korean_text("/".join(parts))
        if is_dir and display:
            display += "/"
        return display

    @classmethod
    def _scan(cls, iso: pycdlib.PyCdlib):
        path_mode = cls._path_mode(iso)
        entries = []
        for directory, dir_names, file_names in iso.walk(**{path_mode: "/"}):
            for dir_name in dir_names:
                source_path = cls._join_iso_path(directory, dir_name)
                display_path = cls._display_path(source_path, path_mode, is_dir=True)
                record = iso.get_record(**{path_mode: source_path})
                is_link = bool(getattr(record, "is_symlink", lambda: False)())
                entries.append({
                    "name": display_path,
                    "source_path": source_path,
                    "size": 0,
                    "compressed_size": 0,
                    "is_dir": True,
                    "is_link": is_link,
                    "date_time": "-",
                })

            for file_name in file_names:
                source_path = cls._join_iso_path(directory, file_name)
                display_path = cls._display_path(source_path, path_mode)
                record = iso.get_record(**{path_mode: source_path})
                is_link = bool(getattr(record, "is_symlink", lambda: False)())
                extents = iso.get_file_byte_extents(**{path_mode: source_path})
                size = sum(length for _, length in extents)
                entries.append({
                    "name": display_path,
                    "source_path": source_path,
                    "size": size,
                    "compressed_size": size,
                    "is_dir": False,
                    "is_link": is_link,
                    "date_time": "-",
                })

        return path_mode, entries

    @classmethod
    def list_contents(cls, file_path: str) -> List[Dict[str, Any]]:
        iso = pycdlib.PyCdlib()
        try:
            iso.open(file_path)
            _, entries = cls._scan(iso)
            validate_entries(entries)
            return [
                {key: value for key, value in entry.items() if key != "source_path"}
                for entry in entries
            ]
        finally:
            iso.close()

    @classmethod
    def extract(
        cls,
        file_path: str,
        target_dir: str,
        selected_files: Optional[List[str]] = None,
        progress_callback=None,
    ) -> List[str]:
        iso = pycdlib.PyCdlib()
        extracted = []
        try:
            iso.open(file_path)
            path_mode, entries = cls._scan(iso)

            selected = None
            if selected_files is not None:
                selected = {name.replace("\\", "/").rstrip("/") for name in selected_files}

            def is_selected(entry):
                if selected is None:
                    return True
                name = entry["name"].rstrip("/")
                return any(name == choice or name.startswith(f"{choice}/") for choice in selected)

            chosen = [entry for entry in entries if is_selected(entry)]
            validate_entries(chosen)
            total = len(chosen)

            for index, entry in enumerate(chosen, start=1):
                if progress_callback:
                    progress_callback(index, total, entry["name"])

                destination = safe_destination(target_dir, entry["name"])
                if entry["is_dir"]:
                    os.makedirs(destination, exist_ok=True)
                    continue

                with iso.open_file_from_iso(**{path_mode: entry["source_path"]}) as source:
                    copy_stream_limited(source, destination, entry["size"])
                extracted.append(destination)

            return extracted
        finally:
            iso.close()

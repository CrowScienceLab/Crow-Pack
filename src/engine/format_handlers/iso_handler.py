"""Read-only ISO 9660/Joliet/Rock Ridge/UDF image support."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

import pycdlib

from ..archive_safety import copy_stream_limited, safe_destination, validate_entries
from ..encoding_helper import normalize_korean_text


class IsoHandler:
    """List and safely copy files from optical-disc images without modifying them."""

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

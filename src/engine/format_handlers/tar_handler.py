"""
Crow Pack - TAR & Compressed TAR Handler
.tar, .tar.gz (.tgz), .tar.bz2 (.tbz2), .tar.xz (.txz) 압축 및 해제 핸들러
"""

import os
import tarfile
from typing import Any, Dict, List, Optional

from ..archive_safety import (
    copy_stream_limited,
    iter_source_files,
    member_is_selected,
    safe_destination,
    validate_entries,
)
from ..encoding_helper import normalize_korean_text


class TarHandler:
    """TAR 및 압축된 TAR(GZ/BZ2/XZ) 핸들러"""

    @staticmethod
    def _get_mode(file_path: str, for_writing: bool = False) -> str:
        """확장자에 따른 tarfile open 모드 판별"""
        ext = file_path.lower()
        if ext.endswith('.tar.gz') or ext.endswith('.tgz'):
            return 'w:gz' if for_writing else 'r:gz'
        elif ext.endswith('.tar.bz2') or ext.endswith('.tbz2'):
            return 'w:bz2' if for_writing else 'r:bz2'
        elif ext.endswith('.tar.xz') or ext.endswith('.txz'):
            return 'w:xz' if for_writing else 'r:xz'
        else:
            return 'w:' if for_writing else 'r:*'

    @classmethod
    def list_contents(cls, file_path: str) -> List[Dict[str, Any]]:
        """TAR 내부 파일 목록 및 메타데이터 조회"""
        items = []
        mode = cls._get_mode(file_path, for_writing=False)
        with tarfile.open(file_path, mode, encoding='utf-8') as tf:
            for member in tf.getmembers():
                clean_name = normalize_korean_text(member.name).replace('\\', '/')
                items.append({
                    "name": clean_name,
                    "size": member.size,
                    "compressed_size": member.size,  # TAR는 스트림 압축이므로 개별 압축 크기는 동일
                    "is_dir": member.isdir(),
                    "date_time": f"{member.mtime}",
                    "mode": oct(member.mode),
                    "type": member.type
                })
        return items

    @classmethod
    def extract(cls, file_path: str, target_dir: str, selected_files: Optional[List[str]] = None,
                progress_callback=None) -> List[str]:
        """TAR 압축 해제 (안전한 경로 추출 & 한글 정규화)"""
        extracted = []
        mode = cls._get_mode(file_path, for_writing=False)
        abs_target_dir = os.path.abspath(target_dir)

        with tarfile.open(file_path, mode, encoding='utf-8') as tf:
            members = tf.getmembers()
            selected_members = []
            entry_metadata = []
            for member in members:
                clean_name = normalize_korean_text(member.name).replace('\\', '/')
                if not member_is_selected(clean_name, selected_files):
                    continue
                selected_members.append((member, clean_name))
                entry_metadata.append({
                    "name": clean_name,
                    "size": member.size,
                    "compressed_size": member.size,
                    "is_link": member.issym() or member.islnk(),
                })
            validate_entries(entry_metadata)
            total = len(members)

            for idx, (member, clean_name) in enumerate(selected_members):

                if progress_callback:
                    progress_callback(idx + 1, total, clean_name)

                dest_path = safe_destination(abs_target_dir, clean_name)

                if member.isdir():
                    os.makedirs(dest_path, exist_ok=True)
                    continue

                if not member.isreg():
                    raise ValueError(f"지원하지 않는 TAR 항목 형식입니다: {clean_name}")

                source_f = tf.extractfile(member)
                if source_f is None:
                    raise ValueError(f"TAR 항목을 읽을 수 없습니다: {clean_name}")
                with source_f:
                    copy_stream_limited(source_f, dest_path, member.size)

                # 파일 수정 시간 복원
                try:
                    os.utime(dest_path, (member.mtime, member.mtime))
                except Exception:
                    pass

                extracted.append(dest_path)

        return extracted

    @classmethod
    def compress(cls, file_paths: List[str], output_path: str, preset: str = "linux",
                 progress_callback=None) -> str:
        """
        TAR 계열 아카이브 생성
        - output_path 확장자에 따라 .tar, .tar.gz, .tar.bz2, .tar.xz 자동 판별
        """
        mode = cls._get_mode(output_path, for_writing=True)
        
        all_targets = list(iter_source_files(file_paths, output_path))

        total = len(all_targets)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        with tarfile.open(output_path, mode, format=tarfile.PAX_FORMAT, encoding='utf-8') as tf:
            for idx, (full_p, rel_p) in enumerate(all_targets):
                clean_name = normalize_korean_text(rel_p).replace('\\', '/')
                if progress_callback:
                    progress_callback(idx + 1, total, clean_name)
                
                tf.add(full_p, arcname=clean_name)

        return output_path

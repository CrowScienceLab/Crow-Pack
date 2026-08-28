"""
Crow Pack - Unified Archive Manager
압축 포맷 및 ISO 이미지 통합 탐색, 해제, 무결성 테스트, 분할 압축 엔진
"""

import os
import tempfile
from typing import Any, Callable, Dict, List, Optional, Tuple

from .format_handlers.iso_handler import IsoHandler
from .format_handlers.korean_format_handler import KoreanFormatHandler
from .format_handlers.seven_zip_handler import CabHandler, RarHandler, SevenZipHandler
from .format_handlers.tar_handler import TarHandler
from .format_handlers.zip_handler import ZipHandler


class ArchiveFormat:
    ZIP = "ZIP"
    ALZ = "ALZ"
    EGG = "EGG"
    SEVEN_ZIP = "7Z"
    RAR = "RAR"
    TAR = "TAR"
    TAR_GZ = "TAR.GZ"
    TAR_BZ2 = "TAR.BZ2"
    TAR_XZ = "TAR.XZ"
    CAB = "CAB"
    ISO = "ISO"
    UNKNOWN = "UNKNOWN"


class ArchiveManager:
    """압축 파일 통합 검사, 해제, 생성, 테스트, 조작 총괄 매니저"""

    @classmethod
    def detect_format(cls, file_path: str) -> str:
        """확장자 및 바이너리 매직 넘버 기반 포맷 판별"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        ext = file_path.lower()

        # 복합 확장자 검사
        if ext.endswith('.tar.gz') or ext.endswith('.tgz'):
            return ArchiveFormat.TAR_GZ
        elif ext.endswith('.tar.bz2') or ext.endswith('.tbz2'):
            return ArchiveFormat.TAR_BZ2
        elif ext.endswith('.tar.xz') or ext.endswith('.txz'):
            return ArchiveFormat.TAR_XZ

        # 단일 확장자 검사
        _, base_ext = os.path.splitext(ext)
        base_ext = base_ext.lstrip('.')

        if base_ext in ['zip', 'jar', 'apk', 'docx', 'xlsx', 'pptx']:
            return ArchiveFormat.ZIP
        elif base_ext == '7z':
            return ArchiveFormat.SEVEN_ZIP
        elif base_ext == 'alz' or KoreanFormatHandler.is_alz(file_path):
            return ArchiveFormat.ALZ
        elif base_ext == 'egg' or KoreanFormatHandler.is_egg(file_path):
            return ArchiveFormat.EGG
        elif base_ext == 'rar':
            return ArchiveFormat.RAR
        elif base_ext == 'tar':
            return ArchiveFormat.TAR
        elif base_ext == 'cab':
            return ArchiveFormat.CAB
        elif base_ext == 'iso':
            return ArchiveFormat.ISO

        # 바이너리 시그니처 폴백
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if header.startswith(b'PK\x03\x04') or header.startswith(b'PK\x05\x06'):
                    return ArchiveFormat.ZIP
                elif header.startswith(b'7z\xbc\xaf\x27\x1c'):
                    return ArchiveFormat.SEVEN_ZIP
                elif header.startswith(b'Rar!\x1a\x07'):
                    return ArchiveFormat.RAR
                elif header.startswith(b'EGGA'):
                    return ArchiveFormat.EGG
                elif header.startswith(b'ALZ\x01') or header.startswith(b'BLZ\x01'):
                    return ArchiveFormat.ALZ
                elif header.startswith(b'MSCF'):
                    return ArchiveFormat.CAB
                f.seek(32 * 1024)
                volume_descriptor = f.read(6)
                if len(volume_descriptor) == 6 and volume_descriptor[1:] == b'CD001':
                    return ArchiveFormat.ISO
        except Exception:
            pass

        return ArchiveFormat.UNKNOWN

    @classmethod
    def list_archive(cls, file_path: str, password: Optional[str] = None, encoding: Optional[str] = None) -> Dict[str, Any]:
        """
        압축 파일 내부 상세 정보 조회 (인코딩/코드페이지 수동 지정 지원)
        """
        fmt = cls.detect_format(file_path)
        items = []

        if fmt == ArchiveFormat.ZIP:
            items = ZipHandler.list_contents(file_path, password=password, encoding=encoding)
        elif fmt == ArchiveFormat.ALZ:
            items = KoreanFormatHandler.list_alz(file_path)
        elif fmt == ArchiveFormat.EGG:
            items = KoreanFormatHandler.list_egg(file_path)
        elif fmt in [ArchiveFormat.TAR, ArchiveFormat.TAR_GZ, ArchiveFormat.TAR_BZ2, ArchiveFormat.TAR_XZ]:
            items = TarHandler.list_contents(file_path)
        elif fmt == ArchiveFormat.SEVEN_ZIP:
            items = SevenZipHandler.list_contents(file_path, password=password)
        elif fmt == ArchiveFormat.RAR:
            items = RarHandler.list_contents(file_path, password=password)
        elif fmt == ArchiveFormat.CAB:
            items = [{"name": os.path.basename(file_path), "size": os.path.getsize(file_path), "compressed_size": os.path.getsize(file_path), "is_dir": False}]
        elif fmt == ArchiveFormat.ISO:
            items = IsoHandler.list_contents(file_path)
        else:
            raise ValueError(f"지원되지 않는 압축 포맷입니다: {fmt}")

        total_uncompressed = sum(item.get("size", 0) for item in items if not item.get("is_dir"))
        total_compressed = sum(item.get("compressed_size", 0) for item in items if not item.get("is_dir"))
        if total_compressed == 0:
            total_compressed = os.path.getsize(file_path)

        file_count = sum(1 for item in items if not item.get("is_dir"))
        dir_count = sum(1 for item in items if item.get("is_dir"))

        # 최상위 루트 폴더 구조 분석 (스마트 알아서 풀기용)
        top_level_names = set()
        for item in items:
            parts = item["name"].strip('/').split('/')
            if parts and parts[0]:
                top_level_names.add(parts[0])

        is_single_root = len(top_level_names) == 1
        root_folder_name = list(top_level_names)[0] if is_single_root else ""

        ratio = 0
        if total_uncompressed > 0:
            ratio = round((1 - (total_compressed / total_uncompressed)) * 100, 1)

        return {
            "format": fmt,
            "filename": os.path.basename(file_path),
            "file_path": os.path.abspath(file_path),
            "archive_size": os.path.getsize(file_path),
            "uncompressed_size": total_uncompressed,
            "compressed_size": total_compressed,
            "compression_ratio": ratio,
            "file_count": file_count,
            "dir_count": dir_count,
            "is_single_root": is_single_root,
            "root_folder_name": root_folder_name,
            "is_read_only": fmt == ArchiveFormat.ISO,
            "items": items
        }

    @classmethod
    def test_archive(cls, file_path: str, password: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """아카이브 파일 무결성 및 손상 검사"""
        fmt = cls.detect_format(file_path)
        if fmt == ArchiveFormat.ZIP:
            return ZipHandler.test_archive(file_path, password=password)
        elif fmt == ArchiveFormat.SEVEN_ZIP:
            return SevenZipHandler.test_archive(file_path, password=password)
        elif fmt == ArchiveFormat.RAR:
            return RarHandler.test_archive(file_path, password=password)
        else:
            # 기타 포맷은 목록 조회 및 헤더 파싱으로 무결성 검증
            try:
                cls.list_archive(file_path, password=password)
                return True, None
            except Exception as e:
                return False, str(e)

    @classmethod
    def extract_single_temp(cls, file_path: str, target_item_name: str, password: Optional[str] = None) -> str:
        """더블클릭 실행을 위해 파일 1개를 임시 폴더에 추출"""
        fmt = cls.detect_format(file_path)
        if fmt == ArchiveFormat.ZIP:
            return ZipHandler.extract_single_file_temp(file_path, target_item_name, password=password)
        elif fmt == ArchiveFormat.SEVEN_ZIP:
            return SevenZipHandler.extract_single_file_temp(file_path, target_item_name, password=password)
        elif fmt == ArchiveFormat.RAR:
            return RarHandler.extract_single_file_temp(file_path, target_item_name, password=password)
        else:
            # 임시 폴더 전체 추출 후 해당 파일 경로 반환
            temp_dir = tempfile.mkdtemp(prefix="crow_pack_preview_")
            _, files = cls.extract_archive(file_path, temp_dir, mode="current", selected_files=[target_item_name], password=password)
            if files:
                return files[0]
            raise FileNotFoundError(f"파일을 추출할 수 없습니다: {target_item_name}")

    @classmethod
    def add_files(cls, archive_path: str, files_to_add: List[str]) -> bool:
        """기존 아카이브에 파일/폴더 추가"""
        fmt = cls.detect_format(archive_path)
        if fmt == ArchiveFormat.ZIP:
            return ZipHandler.add_files_to_zip(archive_path, files_to_add)
        else:
            raise NotImplementedError(f"{fmt} 포맷은 파일 추가를 지원하지 않습니다 (ZIP 권장).")

    @classmethod
    def delete_files(cls, archive_path: str, files_to_delete: List[str]) -> bool:
        """기존 아카이브에서 특정 파일 삭제"""
        fmt = cls.detect_format(archive_path)
        if fmt == ArchiveFormat.ZIP:
            return ZipHandler.delete_files_from_zip(archive_path, files_to_delete)
        else:
            raise NotImplementedError(f"{fmt} 포맷은 파일 삭제를 지원하지 않습니다 (ZIP 권장).")

    @classmethod
    def extract_archive(cls, file_path: str, target_dir: str, mode: str = "smart",
                        selected_files: Optional[List[str]] = None, password: Optional[str] = None,
                        progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Tuple[str, List[str]]:
        """
        압축 해제 실행
        - mode: "smart" (스마트 알아서 풀기 - 단일루트면 그대로, 다중루트면 새폴더 생성하여 난잡함 방지)
                "current" (현재 대상 디렉터리에 바로 풀기)
                "new_folder" (무조건 새 폴더 생성 후 풀기)
        """
        fmt = cls.detect_format(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        if base_name.lower().endswith('.tar'):
            base_name = os.path.splitext(base_name)[0]

        final_dest_dir = os.path.abspath(target_dir)

        if mode == "new_folder":
            final_dest_dir = os.path.join(final_dest_dir, base_name)
        elif mode == "smart":
            try:
                info = cls.list_archive(file_path, password=password)
                if not info["is_single_root"]:
                    final_dest_dir = os.path.join(final_dest_dir, base_name)
            except Exception:
                final_dest_dir = os.path.join(final_dest_dir, base_name)

        os.makedirs(final_dest_dir, exist_ok=True)
        extracted = []

        if fmt == ArchiveFormat.ZIP:
            extracted = ZipHandler.extract(file_path, final_dest_dir, selected_files, password, progress_callback)
        elif fmt == ArchiveFormat.ALZ:
            extracted = KoreanFormatHandler.extract_alz(file_path, final_dest_dir, progress_callback)
        elif fmt == ArchiveFormat.EGG:
            extracted = KoreanFormatHandler.extract_egg(file_path, final_dest_dir, progress_callback)
        elif fmt in [ArchiveFormat.TAR, ArchiveFormat.TAR_GZ, ArchiveFormat.TAR_BZ2, ArchiveFormat.TAR_XZ]:
            extracted = TarHandler.extract(file_path, final_dest_dir, selected_files, progress_callback)
        elif fmt == ArchiveFormat.SEVEN_ZIP:
            extracted = SevenZipHandler.extract(file_path, final_dest_dir, selected_files, password, progress_callback)
        elif fmt == ArchiveFormat.RAR:
            extracted = RarHandler.extract(file_path, final_dest_dir, selected_files, password, progress_callback)
        elif fmt == ArchiveFormat.CAB:
            extracted = CabHandler.extract(file_path, final_dest_dir, progress_callback)
        elif fmt == ArchiveFormat.ISO:
            extracted = IsoHandler.extract(file_path, final_dest_dir, selected_files, progress_callback)
        else:
            raise ValueError(f"지원하지 않는 포맷입니다: {fmt}")

        return final_dest_dir, extracted

    @classmethod
    def create_archive(cls, source_paths: List[str], output_path: str, format_type: str = "ZIP",
                       preset: str = "windows", level: int = 6, password: Optional[str] = None,
                       split_size_mb: int = 0,
                       progress_callback: Optional[Callable[[int, int, str], None]] = None) -> str:
        """
        신규 아카이브 생성 (분할 압축 지원)
        """
        fmt = format_type.upper()

        # 분할 압축 처리 (7Z 포맷 또는 표준 분할)
        if split_size_mb > 0 and fmt == "7Z":
            # py7zr 분할 압축은 단일 생성 후 볼륨 분할 또는 7z 네이티브 생성
            out_file = SevenZipHandler.compress(source_paths, output_path, password=password, level=level, progress_callback=progress_callback)
            cls._split_file(out_file, split_size_mb * 1024 * 1024)
            return out_file

        if fmt == "ZIP":
            out_file = ZipHandler.compress(source_paths, output_path, preset=preset, level=level, password=password, progress_callback=progress_callback)
            if split_size_mb > 0:
                cls._split_file(out_file, split_size_mb * 1024 * 1024)
            return out_file
        elif fmt == "7Z":
            return SevenZipHandler.compress(source_paths, output_path, password=password, level=level, progress_callback=progress_callback)
        elif fmt in ["TAR.GZ", "TAR.XZ", "TAR.BZ2", "TAR", "TGZ", "TXZ"]:
            return TarHandler.compress(source_paths, output_path, preset=preset, progress_callback=progress_callback)
        else:
            return ZipHandler.compress(source_paths, output_path, preset=preset, level=level, password=password, progress_callback=progress_callback)

    @staticmethod
    def _split_file(file_path: str, chunk_size_bytes: int):
        """생성된 파일을 지정된 크기의 볼륨 파일(.001, .002...)로 분할"""
        file_size = os.path.getsize(file_path)
        if file_size <= chunk_size_bytes:
            return

        part_num = 1
        with open(file_path, 'rb') as src_f:
            while chunk := src_f.read(chunk_size_bytes):
                part_path = f"{file_path}.{part_num:03d}"
                with open(part_path, 'wb') as part_f:
                    part_f.write(chunk)
                part_num += 1

"""
Crow Pack - ZIP Handler
표준 ZIP 및 macOS/Windows 호환성 최적화 압축 및 해제 핸들러 (반디집급 고급 기능 지원)
"""

import os
import stat
import tempfile
import zipfile
from typing import Any, Dict, List, Optional, Tuple

import pyzipper

from ..archive_safety import (
    copy_stream_limited,
    iter_source_files,
    member_is_selected,
    safe_destination,
    validate_entries,
)
from ..encoding_helper import fix_zip_filename, normalize_korean_text


class ZipHandler:
    """ZIP 아카이브 압축, 해제, 테스트, 파일 추가/삭제 핸들러"""

    @staticmethod
    def list_contents(file_path: str, password: Optional[str] = None, encoding: Optional[str] = None) -> List[Dict[str, Any]]:
        """ZIP 내부 파일 목록 및 메타데이터 조회 (인코딩 수동/자동 지정)"""
        items = []
        with pyzipper.AESZipFile(file_path, 'r') as zf:
            if password:
                zf.setpassword(password.encode('utf-8'))
            
            for info in zf.infolist():
                if encoding:
                    try:
                        raw_bytes = info.filename.encode('cp437')
                        decoded_name = raw_bytes.decode(encoding, errors='replace')
                    except Exception:
                        decoded_name = info.filename
                else:
                    decoded_name = fix_zip_filename(info.filename, info.flag_bits)

                decoded_name = normalize_korean_text(decoded_name)
                is_dir = info.is_dir() or decoded_name.endswith('/')
                items.append({
                    "name": decoded_name.replace('\\', '/'),
                    "raw_name": info.filename,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "is_dir": is_dir,
                    "crc": info.CRC,
                    "date_time": f"{info.date_time[0]}-{info.date_time[1]:02d}-{info.date_time[2]:02d} {info.date_time[3]:02d}:{info.date_time[4]:02d}",
                    "is_encrypted": bool(info.flag_bits & 0x1)
                })
        return items

    @staticmethod
    def test_archive(file_path: str, password: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """ZIP 아카이브 무결성 및 손상 검사"""
        try:
            with pyzipper.AESZipFile(file_path, 'r') as zf:
                if password:
                    zf.setpassword(password.encode('utf-8'))
                bad_file = zf.testzip()
                if bad_file:
                    return False, f"손상된 파일 발견: {bad_file}"
                return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def extract_single_file_temp(file_path: str, target_item_name: str, password: Optional[str] = None) -> str:
        """더블클릭 실행을 위해 단일 파일을 임시 디렉터리에 추출"""
        temp_dir = tempfile.mkdtemp(prefix="crow_pack_preview_")

        with pyzipper.AESZipFile(file_path, 'r') as zf:
            if password:
                zf.setpassword(password.encode('utf-8'))
            for info in zf.infolist():
                decoded_name = fix_zip_filename(info.filename, info.flag_bits).replace('\\', '/')
                if decoded_name == target_item_name or info.filename == target_item_name:
                    mode = (info.external_attr >> 16) & 0xFFFF
                    validate_entries([{
                        "name": decoded_name,
                        "size": info.file_size,
                        "compressed_size": info.compress_size,
                        "is_link": stat.S_ISLNK(mode),
                    }])
                    base_name = os.path.basename(decoded_name)
                    dest_file = safe_destination(temp_dir, base_name)
                    with zf.open(info, 'r') as source_f:
                        copy_stream_limited(source_f, dest_file, info.file_size)
                    return dest_file
        raise FileNotFoundError(f"아카이브 내에서 파일을 찾을 수 없습니다: {target_item_name}")

    @staticmethod
    def add_files_to_zip(zip_path: str, files_to_add: List[str]) -> bool:
        """기존 ZIP 파일에 새 파일/폴더 추가"""
        with zipfile.ZipFile(zip_path, 'a', compression=zipfile.ZIP_DEFLATED) as zf:
            for p in files_to_add:
                if os.path.isdir(p):
                    base_dir = os.path.dirname(os.path.abspath(p))
                    for root, _, files in os.walk(p):
                        for file in files:
                            full_p = os.path.join(root, file)
                            rel_p = os.path.relpath(full_p, base_dir).replace('\\', '/')
                            zinfo = zipfile.ZipInfo.from_file(full_p, arcname=rel_p)
                            zinfo.flag_bits |= 0x800
                            with open(full_p, 'rb') as f:
                                zf.writestr(zinfo, f.read())
                elif os.path.isfile(p):
                    rel_p = os.path.basename(p)
                    zinfo = zipfile.ZipInfo.from_file(p, arcname=rel_p)
                    zinfo.flag_bits |= 0x800
                    with open(p, 'rb') as f:
                        zf.writestr(zinfo, f.read())
        return True

    @staticmethod
    def delete_files_from_zip(zip_path: str, files_to_delete: List[str]) -> bool:
        """기존 ZIP 파일에서 특정 파일들 삭제"""
        temp_zip = zip_path + ".tmp"
        with zipfile.ZipFile(zip_path, 'r') as zin, zipfile.ZipFile(temp_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                decoded_name = fix_zip_filename(info.filename, info.flag_bits).replace('\\', '/')
                if not member_is_selected(decoded_name, files_to_delete):
                    zout.writestr(info, zin.read(info.filename))
        
        os.replace(temp_zip, zip_path)
        return True

    @staticmethod
    def extract(file_path: str, target_dir: str, selected_files: Optional[List[str]] = None,
                password: Optional[str] = None, progress_callback=None) -> List[str]:
        """ZIP 압축 해제 (파일명 깨짐 방지 및 NFD 정규화)"""
        extracted = []
        with pyzipper.AESZipFile(file_path, 'r') as zf:
            if password:
                zf.setpassword(password.encode('utf-8'))

            infolist = zf.infolist()
            selected_infos = []
            entry_metadata = []
            for info in infolist:
                fixed_name = fix_zip_filename(info.filename, info.flag_bits).replace('\\', '/')
                if not member_is_selected(fixed_name, selected_files):
                    continue
                mode = (info.external_attr >> 16) & 0xFFFF
                selected_infos.append((info, fixed_name))
                entry_metadata.append({
                    "name": fixed_name,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "is_link": stat.S_ISLNK(mode),
                })
            validate_entries(entry_metadata)
            total = len(infolist)

            for idx, (info, fixed_name) in enumerate(selected_infos):

                if progress_callback:
                    progress_callback(idx + 1, total, fixed_name)

                dest_path = safe_destination(target_dir, fixed_name)
                
                if info.is_dir() or fixed_name.endswith('/'):
                    os.makedirs(dest_path, exist_ok=True)
                    continue

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                with zf.open(info, 'r') as source_f:
                    copy_stream_limited(source_f, dest_path, info.file_size)

                try:
                    dt = info.date_time
                    import time
                    t = time.mktime((dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], 0, 0, -1))
                    os.utime(dest_path, (t, t))
                except Exception:
                    pass

                extracted.append(dest_path)

        return extracted

    @staticmethod
    def compress(file_paths: List[str], output_path: str, preset: str = "windows",
                 level: int = 6, password: Optional[str] = None, progress_callback=None) -> str:
        """
        ZIP 파일 생성
        - preset="windows": 표준 Deflate, 윈도우 탐색기 호환
        - preset="macos": UTF-8 플래그 강제 및 NFC 한글 정규화 적용
        - preset="cross": UTF-8 + Deflate 범용 호환
        """
        compress_type = zipfile.ZIP_DEFLATED if level > 0 else zipfile.ZIP_STORED
        compresslevel = max(1, min(9, level)) if level > 0 else None

        all_targets = list(iter_source_files(file_paths, output_path))

        total = len(all_targets)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        kwargs = {"compression": compress_type}
        if compresslevel is not None:
            kwargs["compresslevel"] = compresslevel

        archive_class = pyzipper.AESZipFile if password else zipfile.ZipFile
        if password:
            kwargs["encryption"] = pyzipper.WZ_AES

        with archive_class(output_path, 'w', **kwargs) as zf:
            if password:
                zf.setpassword(password.encode('utf-8'))
                zf.setencryption(pyzipper.WZ_AES, nbits=256)
            for idx, (full_p, rel_p) in enumerate(all_targets):
                normalized_name = normalize_korean_text(rel_p).replace('\\', '/')

                if progress_callback:
                    progress_callback(idx + 1, total, normalized_name)

                zf.write(full_p, arcname=normalized_name)

        return output_path

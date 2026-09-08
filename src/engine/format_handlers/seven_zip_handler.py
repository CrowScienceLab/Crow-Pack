"""
Crow Pack - 7Z, RAR & Miscellaneous Formats Handler
7Z, RAR, CAB 아카이브 압축, 해제, 무결성 테스트, 파일 추가/삭제 핸들러
"""

import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import py7zr
import rarfile

from ..archive_safety import DEFAULT_POLICY, iter_source_files, member_is_selected, safe_destination, validate_entries
from ..encoding_helper import normalize_korean_text


class SevenZipHandler:
    """7Z 포맷 압축, 해제, 테스트 및 조작 핸들러"""

    @staticmethod
    def list_contents(file_path: str, password: Optional[str] = None) -> List[Dict[str, Any]]:
        """7Z 내부 파일 목록 조회"""
        items = []
        with py7zr.SevenZipFile(
            file_path, 'r', password=password, max_extract_size=DEFAULT_POLICY.max_total_size
        ) as archive:
            for info in archive.list():
                clean_name = normalize_korean_text(info.filename).replace('\\', '/')
                items.append({
                    "name": clean_name,
                    "size": info.uncompressed,
                    "compressed_size": info.compressed if hasattr(info, 'compressed') and info.compressed else info.uncompressed,
                    "is_dir": info.is_directory,
                    "is_link": getattr(info, 'is_symlink', False),
                    "crc": getattr(info, 'crc32', 0),
                    "date_time": str(getattr(info, 'creationtime', ''))
                })
        return items

    @staticmethod
    def test_archive(file_path: str, password: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """7Z 아카이브 무결성 검사"""
        try:
            with py7zr.SevenZipFile(
                file_path, 'r', password=password, max_extract_size=DEFAULT_POLICY.max_total_size
            ) as archive:
                is_valid = archive.test()
                if is_valid is False:
                    return False, "7Z 아카이브 내부 데이터 손상 감지"
                return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def extract_single_file_temp(file_path: str, target_item_name: str, password: Optional[str] = None) -> str:
        """더블클릭 실행을 위해 단일 파일을 임시 디렉터리에 추출"""
        temp_dir = tempfile.mkdtemp(prefix="crow_pack_preview_")

        with py7zr.SevenZipFile(
            file_path, 'r', password=password, max_extract_size=DEFAULT_POLICY.max_total_size
        ) as archive:
            matches = [info for info in archive.list() if info.filename == target_item_name]
            if not matches:
                raise FileNotFoundError(f"7Z 아카이브 내에서 파일을 찾을 수 없습니다: {target_item_name}")
            info = matches[0]
            clean_name = normalize_korean_text(info.filename).replace('\\', '/')
            validate_entries([{
                "name": clean_name,
                "size": info.uncompressed,
                "compressed_size": info.compressed or info.uncompressed,
                "is_link": getattr(info, 'is_symlink', False),
            }])
            archive.extract(path=temp_dir, targets=[info.filename])
            dest_file = safe_destination(temp_dir, clean_name)
            if os.path.exists(dest_file):
                return dest_file
        raise FileNotFoundError(f"7Z 아카이브 내에서 파일을 찾을 수 없습니다: {target_item_name}")

    @staticmethod
    def extract(file_path: str, target_dir: str, selected_files: Optional[List[str]] = None,
                password: Optional[str] = None, progress_callback=None) -> List[str]:
        """7Z 압축 해제"""
        extracted = []
        os.makedirs(target_dir, exist_ok=True)

        with py7zr.SevenZipFile(
            file_path, 'r', password=password, max_extract_size=DEFAULT_POLICY.max_total_size
        ) as archive:
            infos = archive.list()
            chosen = []
            entries = []
            for info in infos:
                clean_name = normalize_korean_text(info.filename).replace('\\', '/')
                if not member_is_selected(clean_name, selected_files):
                    continue
                chosen.append(info.filename)
                entries.append({
                    "name": clean_name,
                    "size": info.uncompressed,
                    "compressed_size": info.compressed or info.uncompressed,
                    "is_link": getattr(info, 'is_symlink', False),
                })
            validate_entries(entries)
            targets = chosen if selected_files is not None else None
            archive.extract(path=target_dir, targets=targets)

            for root, _, files in os.walk(target_dir):
                for f in files:
                    extracted.append(os.path.join(root, f))

        if progress_callback:
            progress_callback(100, 100, "완료")

        return extracted

    @staticmethod
    def compress(file_paths: List[str], output_path: str, password: Optional[str] = None,
                 level: int = 6, progress_callback=None) -> str:
        """7Z 아카이브 생성 (LZMA2 / AES-256)"""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        filters = [{'id': py7zr.FILTER_LZMA2, 'preset': max(1, min(9, level))}]
        if password:
            filters.append({'id': py7zr.FILTER_CRYPTO_AES256_SHA256})

        targets = list(iter_source_files(file_paths, output_path))
        with py7zr.SevenZipFile(output_path, 'w', password=password, filters=filters) as archive:
            if password:
                archive.set_encrypted_header(True)
            for full_path, archive_name in targets:
                archive.write(full_path, arcname=normalize_korean_text(archive_name).replace('\\', '/'))

        if progress_callback:
            progress_callback(100, 100, "압축 완료")

        return output_path


class RarHandler:
    """RAR 포맷 해제 핸들러"""

    @staticmethod
    def list_contents(file_path: str, password: Optional[str] = None) -> List[Dict[str, Any]]:
        """RAR 내부 파일 목록 조회"""
        items = []
        with rarfile.RarFile(file_path, 'r') as rf:
            if password:
                rf.setpassword(password)
            for info in rf.infolist():
                clean_name = normalize_korean_text(info.filename).replace('\\', '/')
                items.append({
                    "name": clean_name,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "is_dir": info.isdir(),
                    "date_time": f"{info.date_time[0]}-{info.date_time[1]:02d}-{info.date_time[2]:02d}" if info.date_time else "",
                    "crc": info.CRC
                })
        return items

    @staticmethod
    def test_archive(file_path: str, password: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """RAR 무결성 검사"""
        try:
            with rarfile.RarFile(file_path, 'r') as rf:
                if password:
                    rf.setpassword(password)
                rf.testrar()
                return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def extract_single_file_temp(file_path: str, target_item_name: str, password: Optional[str] = None) -> str:
        """RAR 단일 파일 임시 추출"""
        temp_dir = tempfile.mkdtemp(prefix="crow_pack_preview_")
        with rarfile.RarFile(file_path, 'r') as rf:
            if password:
                rf.setpassword(password)
            info = rf.getinfo(target_item_name)
            clean_name = normalize_korean_text(info.filename).replace('\\', '/')
            validate_entries([{
                "name": clean_name,
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "is_link": info.is_symlink(),
            }])
            rf.extract(info, path=temp_dir)
            dest_file = safe_destination(temp_dir, clean_name)
            if os.path.exists(dest_file):
                return dest_file
        raise FileNotFoundError(f"RAR 파일 내에서 대상을 찾을 수 없습니다: {target_item_name}")

    @staticmethod
    def extract(file_path: str, target_dir: str, selected_files: Optional[List[str]] = None,
                password: Optional[str] = None, progress_callback=None) -> List[str]:
        """RAR 압축 해제"""
        extracted = []
        os.makedirs(target_dir, exist_ok=True)
        with rarfile.RarFile(file_path, 'r') as rf:
            if password:
                rf.setpassword(password)
            
            infolist = rf.infolist()
            chosen_infos = []
            entries = []
            for info in infolist:
                clean_name = normalize_korean_text(info.filename).replace('\\', '/')
                if not member_is_selected(clean_name, selected_files):
                    continue
                chosen_infos.append((info, clean_name))
                entries.append({
                    "name": clean_name,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "is_link": info.is_symlink(),
                })
            validate_entries(entries)
            total = len(infolist)
            for idx, (info, clean_name) in enumerate(chosen_infos):

                if progress_callback:
                    progress_callback(idx + 1, total, clean_name)

                rf.extract(info, path=target_dir)
                extracted.append(safe_destination(target_dir, clean_name))

        return extracted


class CabHandler:
    """CAB (Windows Cabinet) 해제 핸들러"""

    @staticmethod
    def extract(file_path: str, target_dir: str, progress_callback=None) -> List[str]:
        """Windows expand 명령어를 사용한 안전한 CAB 해제"""
        os.makedirs(target_dir, exist_ok=True)
        temp_dir = tempfile.mkdtemp(prefix="crow_pack_cab_")
        result = subprocess.run(
            ["expand.exe", "-F:*", os.path.abspath(file_path), temp_dir],
            shell=False,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"CAB 해제 도구가 오류 코드 {result.returncode}를 반환했습니다.")

        extracted = []
        try:
            for root, _, files in os.walk(temp_dir):
                for filename in files:
                    source = os.path.join(root, filename)
                    relative = os.path.relpath(source, temp_dir).replace('\\', '/')
                    destination = safe_destination(target_dir, relative)
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    shutil.move(source, destination)
                    extracted.append(destination)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        if progress_callback:
            progress_callback(100, 100, "해제 완료")
        return extracted

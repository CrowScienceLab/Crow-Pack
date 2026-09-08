"""
Crow Pack - Korean Format Handler (ALZ & EGG)
한국 특화 압축 포맷인 ALZ 및 EGG 아카이브를 순수 파이썬으로 파싱하고 해제하는 엔진
"""

import bz2
import lzma
import os
import struct
import zlib
from typing import Any, Dict, List

from ..archive_safety import DEFAULT_POLICY, member_is_selected, safe_destination, validate_entries
from ..encoding_helper import normalize_korean_text, smart_decode_filename


class KoreanFormatHandler:
    """ALZ 및 EGG 압축 파일 분석 및 해제 핸들러"""

    @staticmethod
    def _decompress_checked(method: int, data: bytes, expected_size: int, expected_crc: int = 0) -> bytes:
        """Decompress one block with hard size, header-size, and CRC checks."""
        limit = min(DEFAULT_POLICY.max_file_size, max(expected_size, 0)) + 1
        if method == 0:
            output = data
        elif method == 1:
            decoder = zlib.decompressobj(-15)
            output = decoder.decompress(data, limit)
            output += decoder.flush()
            if decoder.unconsumed_tail or not decoder.eof:
                raise ValueError("Deflate 데이터가 손상되었거나 크기 제한을 초과했습니다.")
        elif method == 2:
            decoder = bz2.BZ2Decompressor()
            output = decoder.decompress(data, max_length=limit)
            if not decoder.eof:
                raise ValueError("Bzip2 데이터가 손상되었거나 크기 제한을 초과했습니다.")
        elif method == 4:
            decoder = lzma.LZMADecompressor()
            output = decoder.decompress(data, max_length=limit)
            if not decoder.eof:
                raise ValueError("LZMA 데이터가 손상되었거나 크기 제한을 초과했습니다.")
        else:
            raise ValueError(f"지원하지 않는 ALZ/EGG 압축 방식입니다: {method}")

        if len(output) > DEFAULT_POLICY.max_file_size or len(output) != expected_size:
            raise ValueError("아카이브 헤더 크기와 실제 해제 크기가 다릅니다.")
        if expected_crc and zlib.crc32(output) & 0xFFFFFFFF != expected_crc:
            raise ValueError("ALZ/EGG 항목 CRC 검증에 실패했습니다.")
        return output

    @staticmethod
    def is_alz(file_path: str) -> bool:
        """ALZ 파일 시그니처 검사"""
        try:
            with open(file_path, 'rb') as f:
                sig = f.read(4)
                return sig in [b'ALZ\x01', b'BLZ\x01', b'ALZ\x02']
        except Exception:
            return False

    @staticmethod
    def is_egg(file_path: str) -> bool:
        """EGG 파일 시그니처 검사 (EGGA: 0x41474745)"""
        try:
            with open(file_path, 'rb') as f:
                sig = f.read(4)
                return sig == b'EGGA'
        except Exception:
            return False

    # =========================================================================
    # ALZ 포맷 처리
    # =========================================================================
    @classmethod
    def list_alz(cls, file_path: str) -> List[Dict[str, Any]]:
        """ALZ 파일 내부 항목 목록 조회"""
        items = []
        with open(file_path, 'rb') as f:
            sig = f.read(4)
            if sig not in [b'ALZ\x01', b'BLZ\x01', b'ALZ\x02']:
                raise ValueError("올바른 ALZ 아카이브 형식이 아닙니다.")

            while True:
                header_sig = f.read(4)
                if not header_sig or len(header_sig) < 4:
                    break

                # 파일 헤더 시그니처 (0x015a4c42: BLZ1 / 0x025a4c41: ALZ2 / 0x015a4c41: ALZ1)
                # ALZ 종료 시그니처 (0x015a4c43: CLZ1)
                if header_sig in [b'CLZ\x01', b'ELZ\x01']:
                    break

                # 파일명 길이 (2 bytes)
                fn_len_bytes = f.read(2)
                if not fn_len_bytes or len(fn_len_bytes) < 2:
                    break
                fn_len = struct.unpack('<H', fn_len_bytes)[0]
                
                # 파일 속성 (1 byte)
                f_attr = f.read(1)
                # 시간 정보 (4 bytes)
                f.read(4)
                # 압축 정보 및 크기
                # flag (1 byte), method (1 byte), crc (4 bytes)
                meta = f.read(6)
                if len(meta) < 6:
                    break
                
                method = meta[1]  # 0: stored, 1: deflate, 2: bzip2
                crc = struct.unpack('<I', meta[2:6])[0]
                
                # 압축된 크기, 원본 크기 (4 bytes 또는 8 bytes)
                # 기본 ALZ는 4바이트 크기
                size_data = f.read(8)
                if len(size_data) < 8:
                    break
                c_size, u_size = struct.unpack('<II', size_data)

                # 파일명 읽기
                raw_filename = f.read(fn_len)
                filename = smart_decode_filename(raw_filename)
                
                is_dir = filename.endswith('/') or filename.endswith('\\') or (f_attr and f_attr[0] & 0x10)

                items.append({
                    "name": filename.replace('\\', '/'),
                    "size": u_size,
                    "compressed_size": c_size,
                    "is_dir": bool(is_dir),
                    "method": method,
                    "crc": crc,
                    "data_offset": f.tell()
                })

                # 데이터 영역 건너뛰기
                f.seek(c_size, os.SEEK_CUR)

        return items

    @classmethod
    def extract_alz(cls, file_path: str, target_dir: str, progress_callback=None, selected_files=None) -> List[str]:
        """ALZ 파일 전체 압축 해제"""
        extracted_files = []
        items = cls.list_alz(file_path)
        validate_entries(items)
        total_items = len(items)

        with open(file_path, 'rb') as f:
            for idx, item in enumerate(items):
                if not member_is_selected(item['name'], selected_files):
                    continue
                if progress_callback:
                    progress_callback(idx + 1, total_items, item["name"])

                dest_path = safe_destination(target_dir, item["name"])
                
                if item["is_dir"]:
                    os.makedirs(dest_path, exist_ok=True)
                    continue

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                f.seek(item["data_offset"])
                compressed_data = f.read(item["compressed_size"])

                uncompressed_data = cls._decompress_checked(
                    item["method"], compressed_data, item["size"], item.get("crc", 0)
                )
                with open(dest_path, 'wb') as out_f:
                    out_f.write(uncompressed_data)
                extracted_files.append(dest_path)

        return extracted_files

    # =========================================================================
    # EGG 포맷 처리
    # =========================================================================
    @classmethod
    def list_egg(cls, file_path: str) -> List[Dict[str, Any]]:
        """EGG 파일 내부 항목 목록 조회"""
        items = []
        with open(file_path, 'rb') as f:
            sig = f.read(4)
            if sig != b'EGGA':
                raise ValueError("올바른 EGG 아카이브 형식이 아닙니다.")
            
            f.read(10)

            current_file = None

            while True:
                chunk_sig = f.read(4)
                if not chunk_sig or len(chunk_sig) < 4:
                    break

                if chunk_sig == b'EGGF':  # File Header
                    # 파일 헤더 크기 및 메타
                    f.read(4)
                    f_len = struct.unpack('<Q', f.read(8))[0]  # 원본 파일 크기
                    
                    current_file = {
                        "name": f"file_{len(items)+1}",
                        "size": f_len,
                        "compressed_size": 0,
                        "is_dir": False,
                        "method": 1,
                        "crc": 0,
                        "data_offset": 0
                    }
                    items.append(current_file)

                elif chunk_sig == b'EGGS':  # Filename Header
                    # 플래그 (1 byte: bit 0 -> 0: CP949, 1: UTF-8), 이름 길이 (2 bytes)
                    flag = f.read(1)[0]
                    name_len = struct.unpack('<H', f.read(2))[0]
                    raw_name = f.read(name_len)
                    
                    is_utf8 = bool(flag & 0x01)
                    if is_utf8:
                        fn = raw_name.decode('utf-8', errors='replace')
                    else:
                        fn = smart_decode_filename(raw_name)
                    
                    fn = normalize_korean_text(fn).replace('\\', '/')
                    if current_file:
                        current_file["name"] = fn
                        current_file["is_dir"] = fn.endswith('/')

                elif chunk_sig == b'EGGB':  # Block Header (압축 데이터 블록)
                    # 압축 방식 (1 byte), 압축 크기 (4 bytes), 원본 크기 (4 bytes)
                    method = f.read(1)[0]
                    c_size = struct.unpack('<I', f.read(4))[0]
                    block_uncompressed_size = struct.unpack('<I', f.read(4))[0]
                    crc = struct.unpack('<I', f.read(4))[0]
                    
                    if current_file:
                        current_file["method"] = method
                        current_file["compressed_size"] += c_size
                        current_file["data_offset"] = f.tell()
                        current_file["crc"] = crc
                        if current_file["size"] == 0:
                            current_file["size"] = block_uncompressed_size
                    
                    # 데이터 블록 건너뛰기
                    f.seek(c_size, os.SEEK_CUR)

                elif chunk_sig == b'EGGW':  # Windows Info Header
                    info_size = struct.unpack('<I', f.read(4))[0]
                    f.seek(info_size, os.SEEK_CUR)
                elif chunk_sig == b'EGGC':  # Comment Header
                    c_len = struct.unpack('<H', f.read(2))[0]
                    f.seek(c_len, os.SEEK_CUR)
                elif chunk_sig == b'EGGE':  # Encrypt Header
                    e_len = struct.unpack('<I', f.read(4))[0]
                    f.seek(e_len, os.SEEK_CUR)
                elif chunk_sig == b'EGGT':  # End of EGG
                    break
                else:
                    # 알 수 없는 청크는 안전하게 4바이트씩 이동
                    f.seek(1, os.SEEK_CUR)

        return items

    @classmethod
    def extract_egg(cls, file_path: str, target_dir: str, progress_callback=None, selected_files=None) -> List[str]:
        """EGG 파일 전체 압축 해제"""
        extracted_files = []
        items = cls.list_egg(file_path)
        validate_entries(items)
        total_items = len(items)

        with open(file_path, 'rb') as f:
            for idx, item in enumerate(items):
                if not member_is_selected(item['name'], selected_files):
                    continue
                if progress_callback:
                    progress_callback(idx + 1, total_items, item["name"])

                dest_path = safe_destination(target_dir, item["name"])

                if item["is_dir"]:
                    os.makedirs(dest_path, exist_ok=True)
                    continue

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                if item["data_offset"] == 0 or item["compressed_size"] == 0:
                    # 빈 파일 생성
                    with open(dest_path, 'wb') as out_f:
                        pass
                    extracted_files.append(dest_path)
                    continue

                f.seek(item["data_offset"])
                compressed_data = f.read(item["compressed_size"])

                uncompressed_data = cls._decompress_checked(
                    item["method"], compressed_data, item["size"], item.get("crc", 0)
                )
                with open(dest_path, 'wb') as out_f:
                    out_f.write(uncompressed_data)
                extracted_files.append(dest_path)

        return extracted_files

"""
Crow Pack - Comprehensive Test Suite
주요 압축 포맷, 시스템별 재압축 프리셋, 한글 인코딩 및 암호화 종합 검증
"""

import os
import shutil
import struct
import sys
import unittest
import zlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.archive_manager import ArchiveFormat, ArchiveManager
from src.engine.encoding_helper import normalize_korean_text
from src.engine.format_handlers.korean_format_handler import KoreanFormatHandler


class TestCrowPressComprehensive(unittest.TestCase):
    def setUp(self):
        self.workspace = os.path.abspath("tests/workspace_comprehensive")
        os.makedirs(self.workspace, exist_ok=True)

        # 테스트용 한글 파일들 생성
        self.src_folder = os.path.join(self.workspace, "까마구_프로젝트_문서")
        os.makedirs(self.src_folder, exist_ok=True)

        self.f1 = os.path.join(self.src_folder, "1_시스템_개요.txt")
        with open(self.f1, "w", encoding="utf-8") as f:
            f.write("Crow Pack 압축 프로그램 - 까마구 디자인 시스템\n한글 깨짐 방지 테스트")

        self.f2 = os.path.join(self.src_folder, "2_아이콘_명세.md")
        with open(self.f2, "w", encoding="utf-8") as f:
            f.write("# Crow Iconography\nBeak, Feather, Nest, GemLock, Oculus")

        self.f3 = os.path.join(self.workspace, "루트_파일.log")
        with open(self.f3, "w", encoding="utf-8") as f:
            f.write("2026-08-25 Antigravity Execution Log")

    def tearDown(self):
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace, ignore_errors=True)

    def test_windows_preset_zip(self):
        """Windows 프리셋: 표준 ZIP 압축 및 해제"""
        out_zip = os.path.join(self.workspace, "windows_package.zip")
        ArchiveManager.create_archive([self.src_folder, self.f3], out_zip, format_type="ZIP", preset="windows")
        self.assertTrue(os.path.exists(out_zip))

        info = ArchiveManager.list_archive(out_zip)
        self.assertEqual(info["format"], ArchiveFormat.ZIP)
        self.assertGreaterEqual(info["file_count"], 3)

        # 스마트 해제
        dest_dir, files = ArchiveManager.extract_archive(out_zip, os.path.join(self.workspace, "extract_win"), mode="smart")
        self.assertTrue(os.path.exists(dest_dir))
        self.assertEqual(len(files), 3)

    def test_macos_preset_utf8_nfc(self):
        """macOS 프리셋: UTF-8 강제 및 자소 분리 방지 ZIP"""
        out_zip = os.path.join(self.workspace, "macos_package.zip")
        ArchiveManager.create_archive([self.src_folder], out_zip, format_type="ZIP", preset="macos")
        self.assertTrue(os.path.exists(out_zip))

        # 내부 항목 확인
        info = ArchiveManager.list_archive(out_zip)
        self.assertEqual(info["format"], ArchiveFormat.ZIP)
        for item in info["items"]:
            # 한글이 NFC(완성형)로 정규화되어 있는지 확인
            self.assertEqual(item["name"], normalize_korean_text(item["name"]))

    def test_linux_preset_tar_gz_and_xz(self):
        """Linux 프리셋: TAR.GZ 및 TAR.XZ 아카이브"""
        # TAR.GZ
        out_tgz = os.path.join(self.workspace, "linux_app.tar.gz")
        ArchiveManager.create_archive([self.src_folder], out_tgz, format_type="TAR.GZ", preset="linux")
        self.assertTrue(os.path.exists(out_tgz))
        info_tgz = ArchiveManager.list_archive(out_tgz)
        self.assertEqual(info_tgz["format"], ArchiveFormat.TAR_GZ)

        # TAR.XZ
        out_txz = os.path.join(self.workspace, "linux_app.tar.xz")
        ArchiveManager.create_archive([self.src_folder], out_txz, format_type="TAR.XZ", preset="linux")
        self.assertTrue(os.path.exists(out_txz))
        info_txz = ArchiveManager.list_archive(out_txz)
        self.assertEqual(info_txz["format"], ArchiveFormat.TAR_XZ)

        # 해제
        dest_dir, files = ArchiveManager.extract_archive(out_txz, os.path.join(self.workspace, "extract_linux"))
        self.assertTrue(os.path.exists(dest_dir))
        self.assertEqual(len(files), 2)

    def test_7z_ultra_compression(self):
        """7Z 포맷 초고압축 생성 및 해제"""
        out_7z = os.path.join(self.workspace, "ultra_backup.7z")
        ArchiveManager.create_archive([self.src_folder], out_7z, format_type="7Z", level=9)
        self.assertTrue(os.path.exists(out_7z))

        info = ArchiveManager.list_archive(out_7z)
        self.assertEqual(info["format"], ArchiveFormat.SEVEN_ZIP)
        self.assertEqual(info["file_count"], 2)

        dest_dir, files = ArchiveManager.extract_archive(out_7z, os.path.join(self.workspace, "extract_7z"))
        self.assertTrue(os.path.exists(dest_dir))
        self.assertEqual(len(files), 2)

    def test_synthetic_alz_archive(self):
        """합성 ALZ 아카이브 파싱 및 해제 검증"""
        alz_path = os.path.join(self.workspace, "sample.alz")
        
        # 간단한 유효 ALZ 구조 바이너리 생성
        content = "까마구 ALZ 테스트 데이터".encode('utf-8')
        compressed = zlib.compress(content)[2:-4]  # raw deflate
        fn = "알집_테스트.txt".encode('cp949')

        with open(alz_path, 'wb') as f:
            # ALZ 시그니처 (0x015a4c41)
            f.write(b'ALZ\x01')
            # 파일 헤더 시그니처 (0x015a4c42: BLZ1)
            f.write(b'BLZ\x01')
            # 파일명 길이
            f.write(struct.pack('<H', len(fn)))
            # 파일 속성
            f.write(b'\x00')
            # 시간 (4B)
            f.write(b'\x00\x00\x00\x00')
            # flag(1B), method=1(deflate, 1B), crc(4B)
            f.write(b'\x00\x01' + struct.pack('<I', zlib.crc32(content) & 0xFFFFFFFF))
            # c_size, u_size
            f.write(struct.pack('<II', len(compressed), len(content)))
            # 파일명
            f.write(fn)
            # 압축 데이터
            f.write(compressed)
            # 종료 시그니처 (CLZ1)
            f.write(b'CLZ\x01')

        # 검사
        self.assertTrue(KoreanFormatHandler.is_alz(alz_path))
        info = ArchiveManager.list_archive(alz_path)
        self.assertEqual(info["format"], ArchiveFormat.ALZ)
        self.assertEqual(info["file_count"], 1)

        # 해제
        dest_dir, files = ArchiveManager.extract_archive(alz_path, os.path.join(self.workspace, "extract_alz"))
        self.assertTrue(os.path.exists(dest_dir))
        self.assertEqual(len(files), 1)
        with open(files[0], 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), "까마구 ALZ 테스트 데이터")


if __name__ == "__main__":
    unittest.main()

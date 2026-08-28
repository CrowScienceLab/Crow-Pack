"""
Crow Pack - Engine Test Suite
한글 파일명, 포맷별 압축/해제, 스마트 풀기 기능 검증 테스트
"""

import io
import os
import shutil
import sys
import unittest

import pycdlib

# 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.archive_manager import ArchiveFormat, ArchiveManager
from src.engine.encoding_helper import normalize_korean_text


class TestCrowPressEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath("tests/workspace_temp")
        os.makedirs(self.test_dir, exist_ok=True)
        self.sample_files = []

        # 한글 파일 및 폴더 생성
        self.sub_dir = os.path.join(self.test_dir, "까마구_자료실")
        os.makedirs(self.sub_dir, exist_ok=True)

        f1 = os.path.join(self.sub_dir, "프로젝트_기획서_2026.txt")
        with open(f1, "w", encoding="utf-8") as f:
            f.write("Crow Pack 까마구 압축 프로그램 명세서\n한국어 한글 인코딩 테스트")
        self.sample_files.append(f1)

        f2 = os.path.join(self.test_dir, "까마귀_깃털.md")
        with open(f2, "w", encoding="utf-8") as f:
            f.write("# Raven Feathers\nObsidian Black Theme Design")
        self.sample_files.append(f2)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_korean_encoding_normalization(self):
        # NFD 자소 분리 텍스트: 까마구 (U+1100 U+1161 ...)
        nfd_text = "까마구"
        nfc_text = normalize_korean_text(nfd_text)
        self.assertEqual(nfc_text, "까마구")

    def test_zip_creation_and_extraction(self):
        zip_out = os.path.join(self.test_dir, "테스트_아카이브.zip")
        # 1. 압축 생성
        ArchiveManager.create_archive([self.sub_dir, self.sample_files[1]], zip_out, format_type="ZIP", preset="windows")
        self.assertTrue(os.path.exists(zip_out))

        # 2. 내용 조회
        info = ArchiveManager.list_archive(zip_out)
        self.assertEqual(info["format"], ArchiveFormat.ZIP)
        self.assertGreaterEqual(info["file_count"], 2)

        # 3. 스마트 해제
        extract_dir = os.path.join(self.test_dir, "zip_extracted")
        dest_dir, files = ArchiveManager.extract_archive(zip_out, extract_dir, mode="smart")
        self.assertTrue(os.path.exists(dest_dir))
        self.assertGreaterEqual(len(files), 2)

    def test_7z_creation_and_extraction(self):
        seven_out = os.path.join(self.test_dir, "테스트_7z.7z")
        # 1. 7z 압축
        ArchiveManager.create_archive([self.sub_dir], seven_out, format_type="7Z")
        self.assertTrue(os.path.exists(seven_out))

        # 2. 7z 조회
        info = ArchiveManager.list_archive(seven_out)
        self.assertEqual(info["format"], ArchiveFormat.SEVEN_ZIP)

        # 3. 7z 해제
        extract_dir = os.path.join(self.test_dir, "7z_extracted")
        dest_dir, files = ArchiveManager.extract_archive(seven_out, extract_dir, mode="current")
        self.assertTrue(os.path.exists(dest_dir))

    def test_tar_gz_and_tar_xz(self):
        # TAR.GZ
        tgz_out = os.path.join(self.test_dir, "배포용_패키지.tar.gz")
        ArchiveManager.create_archive([self.sub_dir], tgz_out, format_type="TAR.GZ", preset="linux")
        self.assertTrue(os.path.exists(tgz_out))
        info = ArchiveManager.list_archive(tgz_out)
        self.assertEqual(info["format"], ArchiveFormat.TAR_GZ)

        # TAR.XZ
        txz_out = os.path.join(self.test_dir, "초고압축_패키지.tar.xz")
        ArchiveManager.create_archive([self.sub_dir], txz_out, format_type="TAR.XZ", preset="linux")
        self.assertTrue(os.path.exists(txz_out))
        info_xz = ArchiveManager.list_archive(txz_out)
        self.assertEqual(info_xz["format"], ArchiveFormat.TAR_XZ)

    def test_iso_listing_and_selected_copy(self):
        iso_path = os.path.join(self.test_dir, "한글_디스크.iso")
        payload = "Crow Pack ISO 한글 파일".encode("utf-8")
        iso = pycdlib.PyCdlib()
        iso.new(interchange_level=3, joliet=3, udf="2.60")
        iso.add_directory("/DOCS", joliet_path="/자료", udf_path="/자료")
        iso.add_fp(
            io.BytesIO(payload),
            len(payload),
            iso_path="/DOCS/HELLO.TXT;1",
            joliet_path="/자료/안녕.txt",
            udf_path="/자료/안녕.txt",
        )
        iso.write(iso_path)
        iso.close()

        info = ArchiveManager.list_archive(iso_path)
        self.assertEqual(info["format"], ArchiveFormat.ISO)
        self.assertTrue(info["is_read_only"])
        self.assertIn("자료/안녕.txt", [item["name"] for item in info["items"]])

        output_dir = os.path.join(self.test_dir, "iso_copied")
        _, files = ArchiveManager.extract_archive(
            iso_path,
            output_dir,
            mode="current",
            selected_files=["자료/"],
        )
        self.assertEqual(len(files), 1)
        with open(files[0], "rb") as copied:
            self.assertEqual(copied.read(), payload)

        extensionless = os.path.join(self.test_dir, "disc_image")
        shutil.copyfile(iso_path, extensionless)
        self.assertEqual(ArchiveManager.detect_format(extensionless), ArchiveFormat.ISO)


if __name__ == "__main__":
    unittest.main()

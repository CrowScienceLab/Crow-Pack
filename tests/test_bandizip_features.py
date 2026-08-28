"""
Crow Pack - Bandizip-style Features Unit Tests
무결성 테스트, 파일 추가/삭제, 인코딩 지정, 분할 압축, 단일 파일 임시 추출 테스트
"""

import os
import shutil
import sys
import unittest
import zipfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.archive_manager import ArchiveManager


class TestBandizipFeatures(unittest.TestCase):
    def setUp(self):
        self.workspace = os.path.abspath("tests/workspace_bandi_test")
        os.makedirs(self.workspace, exist_ok=True)

        self.f1 = os.path.join(self.workspace, "문서1.txt")
        with open(self.f1, "w", encoding="utf-8") as f:
            f.write("반디집 스타일 테스트 1번 문서")

        self.f2 = os.path.join(self.workspace, "문서2.txt")
        with open(self.f2, "w", encoding="utf-8") as f:
            f.write("반디집 스타일 테스트 2번 문서")

    def tearDown(self):
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace, ignore_errors=True)

    def test_archive_integrity_test(self):
        """무결성 검사 테스트"""
        zip_path = os.path.join(self.workspace, "test.zip")
        ArchiveManager.create_archive([self.f1], zip_path, format_type="ZIP")
        
        is_valid, err = ArchiveManager.test_archive(zip_path)
        self.assertTrue(is_valid)
        self.assertIsNone(err)

    def test_add_and_delete_files_in_archive(self):
        """아카이브 내 파일 추가 및 삭제 테스트"""
        zip_path = os.path.join(self.workspace, "manipulate.zip")
        ArchiveManager.create_archive([self.f1], zip_path, format_type="ZIP")

        # 파일 추가
        ArchiveManager.add_files(zip_path, [self.f2])
        info = ArchiveManager.list_archive(zip_path)
        self.assertEqual(info["file_count"], 2)

        # 파일 삭제
        ArchiveManager.delete_files(zip_path, ["문서1.txt"])
        info2 = ArchiveManager.list_archive(zip_path)
        self.assertEqual(info2["file_count"], 1)
        self.assertEqual(info2["items"][0]["name"], "문서2.txt")

    def test_delete_selected_directory_in_zip(self):
        zip_path = os.path.join(self.workspace, "directory_delete.zip")
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("폴더/a.txt", "a")
            archive.writestr("폴더/하위/b.txt", "b")
            archive.writestr("keep.txt", "keep")

        ArchiveManager.delete_files(zip_path, ["폴더/"])
        names = [item["name"] for item in ArchiveManager.list_archive(zip_path)["items"]]
        self.assertEqual(names, ["keep.txt"])

    def test_single_file_temp_extraction(self):
        """더블클릭 실행을 위한 단일 파일 임시 추출 테스트"""
        zip_path = os.path.join(self.workspace, "preview.zip")
        ArchiveManager.create_archive([self.f1, self.f2], zip_path, format_type="ZIP")

        temp_path = ArchiveManager.extract_single_temp(zip_path, "문서1.txt")
        self.assertTrue(os.path.exists(temp_path))
        with open(temp_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "반디집 스타일 테스트 1번 문서")

    def test_split_archive_creation(self):
        """분할 압축 생성 테스트"""
        # 더미 난수 데이터 생성 (1.5MB - 압축 후에도 1MB 초과)
        large_file = os.path.join(self.workspace, "large.dat")
        with open(large_file, "wb") as f:
            f.write(os.urandom(1500 * 1024))

        out_zip = os.path.join(self.workspace, "split_test.zip")
        # 1MB 단위 분할
        ArchiveManager.create_archive([large_file], out_zip, format_type="ZIP", split_size_mb=1)
        self.assertTrue(os.path.exists(out_zip))
        self.assertTrue(os.path.exists(out_zip + ".001"))
        self.assertTrue(os.path.exists(out_zip + ".002"))


if __name__ == "__main__":
    unittest.main()

"""Security regression tests for hostile archive metadata."""

import io
import os
import stat
import sys
import tarfile
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pyzipper

from src.engine.archive_manager import ArchiveManager
from src.engine.archive_safety import ArchiveSecurityError, normalize_member_name


class TestArchiveSecurity(unittest.TestCase):
    def test_rejects_parent_absolute_drive_and_reserved_names(self):
        for name in ("../escape.txt", "/absolute.txt", "C:/escape.txt", "folder/CON.txt"):
            with self.subTest(name=name), self.assertRaises(ArchiveSecurityError):
                normalize_member_name(name)

    def test_zip_slip_is_blocked(self):
        with tempfile.TemporaryDirectory() as workspace:
            archive_path = os.path.join(workspace, "hostile.zip")
            destination = os.path.join(workspace, "out")
            escape_path = os.path.join(workspace, "escape.txt")
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../escape.txt", "blocked")

            with self.assertRaises(ArchiveSecurityError):
                ArchiveManager.extract_archive(archive_path, destination, mode="current")
            self.assertFalse(os.path.exists(escape_path))

    def test_zip_symlink_is_blocked(self):
        with tempfile.TemporaryDirectory() as workspace:
            archive_path = os.path.join(workspace, "symlink.zip")
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(info, "../outside.txt")

            with self.assertRaises(ArchiveSecurityError):
                ArchiveManager.extract_archive(archive_path, os.path.join(workspace, "out"), mode="current")

    def test_tar_slip_and_links_are_blocked(self):
        with tempfile.TemporaryDirectory() as workspace:
            archive_path = os.path.join(workspace, "hostile.tar")
            with tarfile.open(archive_path, "w") as archive:
                traversal = tarfile.TarInfo("../escape.txt")
                traversal.size = 1
                archive.addfile(traversal, io.BytesIO(b"x"))
            with self.assertRaises(ArchiveSecurityError):
                ArchiveManager.extract_archive(archive_path, os.path.join(workspace, "out"), mode="current")

            link_path = os.path.join(workspace, "link.tar")
            with tarfile.open(link_path, "w") as archive:
                link = tarfile.TarInfo("shortcut")
                link.type = tarfile.SYMTYPE
                link.linkname = "../outside"
                archive.addfile(link)
            with self.assertRaises(ArchiveSecurityError):
                ArchiveManager.extract_archive(link_path, os.path.join(workspace, "link-out"), mode="current")

    def test_zip_password_uses_aes(self):
        with tempfile.TemporaryDirectory() as workspace:
            source = os.path.join(workspace, "secret.txt")
            archive_path = os.path.join(workspace, "secret.zip")
            with open(source, "w", encoding="utf-8") as handle:
                handle.write("private test data")

            ArchiveManager.create_archive([source], archive_path, format_type="ZIP", password="correct horse")
            with pyzipper.AESZipFile(archive_path) as archive:
                archive.setpassword(b"correct horse")
                self.assertEqual(archive.read("secret.txt"), b"private test data")
            with pyzipper.AESZipFile(archive_path) as archive:
                with self.assertRaises(RuntimeError):
                    archive.read("secret.txt")


if __name__ == "__main__":
    unittest.main()

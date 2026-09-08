"""v1.5 end-to-end engine regression and security tests."""

import hashlib
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from src.engine.archive_manager import ArchiveManager as AM
from src.engine.archive_safety import ArchiveSecurityError
from src.engine.packaging_tools import (
    DragExportManager,
    batch_extract,
    checksum_manifest,
    convert_archive,
    create_cbz,
    sha256,
    verify_checksum,
)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "학생 자료.txt"
        self.source.write_text("Crow Pack sample", encoding="utf-8")

    def archive(self, fmt="ZIP", password=None):
        output = self.root / ("source." + fmt.lower())
        AM.create_archive([str(self.source)], str(output), fmt, password=password)
        return str(output)

    def test_private_7z_headers_and_payload(self):
        path = self.archive("7Z", "a private test passphrase")
        with self.assertRaises(Exception):
            AM.list_archive(path)
        with self.assertRaises(Exception):
            AM.extract_archive(path, str(self.root / "wrong"), "current", password="wrong")
        info = AM.list_archive(path, "a private test passphrase")
        self.assertEqual(info["items"][0]["name"], self.source.name)
        _, files = AM.extract_archive(path, str(self.root / "valid"), "current", password="a private test passphrase")
        self.assertEqual(Path(files[0]).read_bytes(), self.source.read_bytes())

    def test_cbz_natural_order_and_selection(self):
        images = []
        from PIL import Image

        for number in [10, 1, 2]:
            path = self.root / f"{number}.png"
            Image.new("RGB", (10, 10), (number, 0, 0)).save(path)
            images.append(str(path))
        output = str(self.root / "comic.cbz")
        create_cbz(images, output)
        info = AM.list_archive(output)
        self.assertEqual([i["name"] for i in info["items"]], ["001.png", "002.png", "003.png"])
        _, files = AM.extract_archive(output, str(self.root / "pages"), "current", ["002.png"])
        self.assertEqual(len(files), 1)
        with Image.open(files[0]) as page:
            self.assertEqual(page.getpixel((0, 0)), (2, 0, 0))
        with self.assertRaises(FileExistsError):
            create_cbz(images, output)

    def test_conversion_roundtrips(self):
        for source_fmt, target_fmt in [("ZIP", "7Z"), ("7Z", "ZIP"), ("TAR.GZ", "ZIP")]:
            with self.subTest(source_fmt=source_fmt):
                source = self.archive(source_fmt)
                before = sha256(source)
                output = str(self.root / (source_fmt + ".result." + target_fmt.lower()))
                convert_archive(source, output, target_fmt)
                self.assertEqual(sha256(source), before)
                _, files = AM.extract_archive(output, str(self.root / source_fmt), "current")
                self.assertEqual(Path(files[0]).read_bytes(), self.source.read_bytes())

    def test_encrypted_conversion_and_source_preservation(self):
        source = self.archive("ZIP", "secret")
        before = sha256(source)
        output = str(self.root / "private.7z")
        with self.assertRaises(Exception):
            convert_archive(source, output, "7Z", "wrong")
        self.assertFalse(os.path.exists(output))
        self.assertEqual(sha256(source), before)
        convert_archive(source, output, "7Z", "secret", "new secret")
        self.assertTrue(AM.list_archive(output, "new secret")["items"])
        with self.assertRaises(FileExistsError):
            convert_archive(source, output, "7Z", "secret")

    def test_checksum_stream_manifest_and_compare(self):
        self.source.write_bytes(b"abc")
        expected = hashlib.sha256(b"abc").hexdigest()
        self.assertEqual(sha256(self.source), expected)
        self.assertTrue(verify_checksum(self.source, expected)["matches"])
        self.assertFalse(verify_checksum(self.source, "0" * 64)["matches"])
        with self.assertRaises(ValueError):
            verify_checksum(self.source, "not a hash")
        large = self.root / "large.bin"
        with large.open("wb") as stream:
            for _ in range(20):
                stream.write(b"x" * 1024 * 1024)
        callbacks = []
        sha256(large, lambda *args: callbacks.append(args))
        self.assertGreater(len(callbacks), 1)
        manifest = self.root / "SHA256SUMS.txt"
        checksum_manifest([str(self.source), str(large)], str(manifest))
        self.assertIn(expected, manifest.read_text(encoding="utf-8"))
        self.assertEqual(len(manifest.read_text(encoding="utf-8").splitlines()), 2)

    def test_batch_mixed_partial_failure_and_collisions(self):
        zip_path = self.archive()
        seven = self.archive("7Z", "secret")
        broken = self.root / "broken.zip"
        broken.write_bytes(b"bad")
        paths = [zip_path, str(broken), seven, zip_path]
        results = batch_extract(paths, str(self.root / "batch"), password="secret")
        self.assertEqual([r["success"] for r in results], [True, False, True, True])
        self.assertNotEqual(results[0]["output_dir"], results[3]["output_dir"])

    def test_drag_formats_selected_and_unicode(self):
        manager = DragExportManager(self.root / "drag")
        for fmt in ["ZIP", "7Z", "TAR.GZ"]:
            source = self.archive(fmt)
            paths = manager.prepare(source, [self.source.name])
            self.assertEqual(len(paths), 1)
            self.assertEqual(Path(paths[0]).read_bytes(), self.source.read_bytes())
        iso = str(self.root / "disc.iso")
        AM.create_iso([str(self.source)], iso)
        entries = AM.list_archive(iso)["items"]
        paths = manager.prepare(iso, [e["name"] for e in entries if not e["is_dir"]])
        self.assertEqual(Path(paths[0]).read_bytes(), self.source.read_bytes())
        manager.close()
        self.assertTrue(Path(paths[0]).exists())

    def test_drag_traversal_cancel_and_stale_cleanup(self):
        bad = self.root / "bad.zip"
        with zipfile.ZipFile(bad, "w") as archive:
            archive.writestr("../escape.txt", "evil")
        manager = DragExportManager(self.root / "drag")
        with self.assertRaises(ArchiveSecurityError):
            manager.prepare(str(bad), ["../escape.txt"])
        with self.assertRaises(ValueError):
            manager.prepare(str(bad), [])
        other = manager.root / "other-app"
        other.mkdir()
        os.utime(manager.session, (1, 1))
        manager.cleanup_old()
        self.assertFalse(manager.session.exists())
        self.assertTrue(other.exists())

    def test_split_archive_creates_numbered_volumes(self):
        source = self.root / "large.bin"
        source.write_bytes(os.urandom(2 * 1024 * 1024 + 17))
        output = self.root / "volumes.zip"
        AM.create_archive([str(source)], str(output), "ZIP", split_size_mb=1)
        self.assertTrue(output.exists())
        parts = sorted(self.root.glob("volumes.zip.*"))
        self.assertGreaterEqual(len(parts), 2)
        self.assertEqual(b"".join(part.read_bytes() for part in parts), output.read_bytes())


if __name__ == "__main__":
    unittest.main()

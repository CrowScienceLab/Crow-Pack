"""Bridge-level preview and status tests."""

import hashlib
import io
import json
import os
import shutil
import unittest
import zipfile
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

from src.bridge.core_bridge import CoreBridge
from src.engine.pdf_optimizer import PdfOptimizer


class TestBridgeFeatures(unittest.TestCase):
    def setUp(self):
        self.workspace = os.path.abspath("tests/workspace_bridge_features")
        os.makedirs(self.workspace, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_image_preview_returns_thumbnail_data_url(self):
        image_path = os.path.join(self.workspace, "sample.png")
        image = QImage(32, 24, QImage.Format_RGB32)
        image.fill(Qt.cyan)
        self.assertTrue(image.save(image_path, "PNG"))
        zip_path = os.path.join(self.workspace, "images.zip")
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.write(image_path, "sample.png")

        result = json.loads(CoreBridge().getImagePreview(zip_path, "sample.png", ""))

        self.assertTrue(result["success"])
        self.assertTrue(result["data_url"].startswith("data:image/png;base64,"))
        self.assertEqual((result["width"], result["height"]), (32, 24))

    def test_update_status_reports_current_version(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = json.dumps({
            "tag_name": "v1.5.3",
            "html_url": "https://github.com/CrowScienceLab/Crow-Pack/releases/tag/v1.5.3",
        }).encode("utf-8")
        with patch("src.bridge.core_bridge.urllib.request.urlopen", return_value=response):
            result = json.loads(CoreBridge().checkForUpdates())
        self.assertTrue(result["success"])
        self.assertEqual(result["version"], "1.5.3")
        self.assertFalse(result["update_available"])

    def test_update_status_exposes_verified_newer_installer(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = json.dumps({
            "tag_name": "v1.5.4",
            "html_url": "https://github.com/CrowScienceLab/Crow-Pack/releases/tag/v1.5.4",
            "assets": [{
                "name": "CrowPack-v1.5.4-Setup-x64.exe",
                "browser_download_url": "https://github.com/CrowScienceLab/Crow-Pack/releases/download/v1.5.4/CrowPack-v1.5.4-Setup-x64.exe",
                "digest": "sha256:" + "a" * 64,
                "size": 123456,
            }],
        }).encode("utf-8")
        with patch("src.bridge.core_bridge.urllib.request.urlopen", return_value=response):
            result = json.loads(CoreBridge().checkForUpdates())
        self.assertTrue(result["update_available"])
        self.assertEqual(result["latest_tag"], "v1.5.4")
        self.assertEqual(result["sha256"], "a" * 64)

    def test_store_managed_update_uses_store_without_installer_asset(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = json.dumps({
            "tag_name": "v1.5.4",
            "html_url": "https://github.com/CrowScienceLab/Crow-Pack/releases/tag/v1.5.4",
            "assets": [],
        }).encode("utf-8")
        with (
            patch("src.bridge.core_bridge.urllib.request.urlopen", return_value=response),
            patch.object(CoreBridge, "_is_packaged", return_value=True),
        ):
            result = json.loads(CoreBridge().checkForUpdates())
        self.assertTrue(result["update_available"])
        self.assertTrue(result["store_managed"])
        self.assertEqual(result["store_url"], "ms-windows-store://pdp/?productid=9NPBKL0XTKQ7")
        self.assertNotIn("download_url", result)

    def test_distribution_info_reports_github_channel_when_unpacked(self):
        with patch.object(CoreBridge, "_is_packaged", return_value=False):
            result = json.loads(CoreBridge().getDistributionInfo())
        self.assertEqual(result["channel"], "github")
        self.assertFalse(result["packaged"])
        self.assertEqual(result["store_id"], "9NPBKL0XTKQ7")

    def test_older_release_is_not_an_update(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = json.dumps({"tag_name": "v1.5.0"}).encode("utf-8")
        with patch("src.bridge.core_bridge.urllib.request.urlopen", return_value=response):
            result = json.loads(CoreBridge().checkForUpdates())
        self.assertFalse(result["update_available"])

    def test_approved_update_download_is_hash_checked_before_launch(self):
        payload = b"Crow Pack signed installer fixture"
        release = {
            "tag_name": "v1.5.4",
            "assets": [{
                "name": "CrowPack-v1.5.4-Setup-x64.exe",
                "browser_download_url": "https://github.com/CrowScienceLab/Crow-Pack/releases/download/v1.5.4/CrowPack-v1.5.4-Setup-x64.exe",
                "digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
            }],
        }
        api_response = io.BytesIO(json.dumps(release).encode("utf-8"))
        installer_response = io.BytesIO(payload)
        bridge = CoreBridge()
        with (
            patch.dict(os.environ, {"LOCALAPPDATA": self.workspace}),
            patch("src.bridge.core_bridge.urllib.request.urlopen", side_effect=[api_response, installer_response]),
            patch("src.bridge.core_bridge.subprocess.Popen") as launch,
        ):
            bridge.downloadAndInstallUpdate("v1.5.4")
            bridge._update_job.join(timeout=5)
        self.assertFalse(bridge._update_job.is_alive())
        installer = os.path.join(self.workspace, "Crow Pack", "Updates", "CrowPack-v1.5.4-Setup-x64.exe")
        with open(installer, "rb") as stream:
            self.assertEqual(stream.read(), payload)
        launch.assert_called_once()

    def test_update_status_reports_network_error(self):
        with patch("src.bridge.core_bridge.urllib.request.urlopen", side_effect=URLError("offline")):
            result = json.loads(CoreBridge().checkForUpdates())
        self.assertFalse(result["success"])
        self.assertIn("GitHub", result["error"])

    def test_context_copy_and_move_zip_items(self):
        source_path = os.path.join(self.workspace, "source.txt")
        with open(source_path, "w", encoding="utf-8") as source:
            source.write("Crow Pack context action")
        archive_path = os.path.join(self.workspace, "actions.zip")
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.write(source_path, "folder/source.txt")

        copy_dir = os.path.join(self.workspace, "copied")
        os.makedirs(copy_dir)
        with patch("src.bridge.core_bridge.QFileDialog.getExistingDirectory", return_value=copy_dir):
            copied = json.loads(CoreBridge().exportArchiveItems(
                archive_path,
                json.dumps(["folder/source.txt"]),
                False,
            ))
        self.assertTrue(copied["success"])
        self.assertTrue(os.path.isfile(os.path.join(copy_dir, "folder", "source.txt")))

        move_dir = os.path.join(self.workspace, "moved")
        os.makedirs(move_dir)
        with patch("src.bridge.core_bridge.QFileDialog.getExistingDirectory", return_value=move_dir):
            moved = json.loads(CoreBridge().exportArchiveItems(
                archive_path,
                json.dumps(["folder/source.txt"]),
                True,
            ))
        self.assertTrue(moved["success"])
        self.assertTrue(os.path.isfile(os.path.join(move_dir, "folder", "source.txt")))
        with zipfile.ZipFile(archive_path) as archive:
            self.assertNotIn("folder/source.txt", archive.namelist())

    def test_pdf_preset_backend_forwards_selected_profile(self):
        input_path = os.path.join(self.workspace, "source.pdf")
        output_path = os.path.join(self.workspace, "optimized.pdf")
        expected = {
            "success": True,
            "output_path": output_path,
            "saved_bytes": 123,
            "message": "PDF 무손실 정리가 완료되었습니다.",
        }
        with (
            patch("src.bridge.core_bridge.QFileDialog.getOpenFileName", return_value=(input_path, "PDF")),
            patch("src.bridge.core_bridge.QFileDialog.getSaveFileName", return_value=(output_path, "PDF")),
            patch.object(PdfOptimizer, "optimize", return_value=expected.copy()) as optimize,
        ):
            result = json.loads(CoreBridge().optimizePdfPreset("balanced"))
        self.assertTrue(result["success"])
        self.assertEqual(result["output_path"], output_path)
        optimize.assert_called_once_with(input_path, output_path, preset="balanced")

    def test_iso_creation_bridge_uses_save_dialog(self):
        source = os.path.join(self.workspace, "자료.txt")
        output = os.path.join(self.workspace, "자료.iso")
        with open(source, "w", encoding="utf-8") as stream:
            stream.write("Crow Pack")
        with patch("src.bridge.core_bridge.QFileDialog.getSaveFileName", return_value=(output, "ISO")):
            result = json.loads(CoreBridge().createIsoImage(json.dumps([source]), "CROW_PACK"))
        self.assertTrue(result["success"])
        self.assertTrue(os.path.isfile(output))

    def test_association_button_registers_candidate_and_opens_settings(self):
        fake_key = MagicMock()
        fake_key.__enter__.return_value = fake_key
        with (
            patch("src.engine.shell_integration.winreg.CreateKey", return_value=fake_key) as create_key,
            patch("src.engine.shell_integration.winreg.SetValueEx") as set_value,
            patch("src.engine.shell_integration.winreg.OpenKey", side_effect=FileNotFoundError),
            patch("src.engine.shell_integration.winreg.QueryValueEx", side_effect=FileNotFoundError),
            patch("src.bridge.core_bridge.os.startfile") as start_file,
        ):
            result = json.loads(CoreBridge().registerFileAssociations())
        self.assertTrue(result["success"])
        self.assertGreater(create_key.call_count, 4)
        self.assertGreater(set_value.call_count, 10)
        self.assertIn('.cbz', result['registered_extensions'])
        self.assertNotIn('.docx', result['registered_extensions'])
        self.assertFalse(any('UserChoice' in str(call) for call in create_key.call_args_list))
        start_file.assert_called_once_with("ms-settings:defaultapps?registeredAppUser=Crow%20Pack")


if __name__ == "__main__":
    unittest.main()

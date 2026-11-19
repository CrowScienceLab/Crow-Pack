"""Regression checks for Windows distribution and file activation contracts."""

import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.bridge.core_bridge import CoreBridge
from src.engine.shell_integration import EXTENSIONS, STORE_AUMID, _can_set_legacy_default, create_desktop_shortcut

ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def test_existing_windows_choice_blocks_legacy_default(self):
        with patch('src.engine.shell_integration.winreg.OpenKey', return_value=MagicMock()) as open_key, \
                patch('src.engine.shell_integration._association_value') as association:
            self.assertFalse(_can_set_legacy_default('.zip'))
        self.assertTrue(open_key.call_args.args[1].endswith(r'.zip\UserChoice'))
        association.assert_not_called()

    def test_unassigned_legacy_default_checks_effective_windows_association(self):
        with patch('src.engine.shell_integration.winreg.OpenKey', side_effect=FileNotFoundError), \
                patch('src.engine.shell_integration._association_value', return_value='') as association:
            self.assertTrue(_can_set_legacy_default('.zip'))
            association.return_value = 'Another.Application'
            self.assertFalse(_can_set_legacy_default('.zip'))

    def test_windows_shortcut_does_not_replace_existing_different_link(self):
        with tempfile.TemporaryDirectory() as workspace:
            desktop = Path(workspace)
            self.assertEqual(create_desktop_shortcut(desktop, False), 'created')
            self.assertEqual(create_desktop_shortcut(desktop, False), 'exists')
            existing = (desktop / 'CrowPack.lnk').read_bytes()
            with patch.object(sys, 'executable', str(desktop / 'Another.exe')), self.assertRaises(FileExistsError):
                create_desktop_shortcut(desktop, False)
            self.assertEqual((desktop / 'CrowPack.lnk').read_bytes(), existing)

    def test_store_default_apps_uses_package_identity(self):
        with patch.object(CoreBridge, '_is_packaged', return_value=True), \
                patch('src.bridge.tools_bridge.os.startfile') as launch:
            CoreBridge().openDefaultApps()
        self.assertIn('registeredAUMID=', launch.call_args.args[0])
        self.assertIn('%21CrowPack', launch.call_args.args[0])
        self.assertIn(STORE_AUMID.split('!')[0], launch.call_args.args[0])

    def test_installer_default_apps_repairs_registration_before_opening(self):
        calls = []
        with patch.object(CoreBridge, '_is_packaged', return_value=False), \
                patch('src.engine.shell_integration.register', side_effect=lambda **kw: calls.append(kw)), \
                patch('src.bridge.tools_bridge.os.startfile', side_effect=lambda uri: calls.append(uri)):
            CoreBridge().openDefaultApps()
        self.assertEqual(calls[0], {'menu': False})
        self.assertIn('registeredAppUser=', calls[1])

    def test_store_file_activation_and_version_match_desktop(self):
        root = ET.parse(ROOT / 'store/AppxManifest.xml').getroot()  # noqa: S314 - trusted repository manifest
        ns = {'f': 'http://schemas.microsoft.com/appx/manifest/foundation/windows10',
              'u': 'http://schemas.microsoft.com/appx/manifest/uap/windows10',
              'u3': 'http://schemas.microsoft.com/appx/manifest/uap/windows10/3'}
        self.assertEqual(root.find('f:Identity', ns).get('Version'), '.'.join((CoreBridge.APP_VERSION.split('.') + ['0'] * 4)[:4]))
        association = root.find('.//u3:FileTypeAssociation', ns)
        self.assertEqual(association.get('Parameters'), '"%1"')
        extensions = {node.text for node in association.findall('.//u:FileType', ns)}
        self.assertEqual(extensions, set(EXTENSIONS))
        # Versioned distribution metadata also comes from the running application.
        self.assertIn('channel', json.loads(CoreBridge().getDistributionInfo()))


if __name__ == '__main__':
    unittest.main()

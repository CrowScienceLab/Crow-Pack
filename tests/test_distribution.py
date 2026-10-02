"""Regression checks for Windows distribution and file activation contracts."""

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from src.bridge.core_bridge import CoreBridge
from src.engine.shell_integration import EXTENSIONS

ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def test_store_default_apps_uses_package_identity(self):
        with patch.object(CoreBridge, '_is_packaged', return_value=True), \
                patch('src.bridge.tools_bridge.os.startfile') as launch:
            CoreBridge().openDefaultApps()
        self.assertIn('registeredAUMID=', launch.call_args.args[0])
        self.assertIn('%21CrowPack', launch.call_args.args[0])

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
        self.assertEqual(root.find('f:Identity', ns).get('Version'), CoreBridge.APP_VERSION + '.0')
        association = root.find('.//u3:FileTypeAssociation', ns)
        self.assertEqual(association.get('Parameters'), '"%1"')
        extensions = {node.text for node in association.findall('.//u:FileType', ns)}
        self.assertEqual(extensions, set(EXTENSIONS))
        # Versioned distribution metadata also comes from the running application.
        self.assertIn('channel', json.loads(CoreBridge().getDistributionInfo()))


if __name__ == '__main__':
    unittest.main()

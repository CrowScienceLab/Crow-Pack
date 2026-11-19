"""Failed checks are unknown, not proof that the installed app is current."""
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from src.bridge.core_bridge import CoreBridge


class UpdateDiagnosticsTests(unittest.TestCase):
    def test_public_three_part_alias_compares_equal_to_1_7(self):
        self.assertEqual(CoreBridge._version_tuple('v1.7'), CoreBridge._version_tuple('v1.7.0'))
        self.assertGreater(CoreBridge._version_tuple('v1.7.1'), CoreBridge._version_tuple('v1.7'))

    def test_store_route_does_not_start_github_download(self):
        bridge = CoreBridge()
        with patch.object(bridge, '_is_packaged', return_value=True), \
                patch('src.bridge.core_bridge.urllib.request.urlopen') as request:
            bridge.downloadAndInstallUpdate('v1.7.1')
        request.assert_not_called()
        self.assertIsNone(bridge._update_job)

    def test_rate_limit_has_actionable_reason(self):
        error = HTTPError(CoreBridge.LATEST_RELEASE_API, 403, 'Forbidden', {'X-RateLimit-Remaining': '0'}, None)
        with patch('src.bridge.core_bridge.urllib.request.urlopen', side_effect=error):
            result = json.loads(CoreBridge().checkForUpdates())
        self.assertFalse(result['success'])
        self.assertEqual(result.get('error_code'), 'rate_limit')

    def test_invalid_api_payload_does_not_lose_async_result(self):
        with patch('src.bridge.core_bridge.urllib.request.urlopen', return_value=io.BytesIO(b'[]')):
            result = json.loads(CoreBridge().checkForUpdates())
        self.assertFalse(result['success'])
        self.assertEqual(result.get('error_code'), 'invalid_response')

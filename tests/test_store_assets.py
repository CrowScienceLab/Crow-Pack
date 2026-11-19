"""Store shell icons must not carry tile padding and need qualified variants."""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.build_msix import _asset, generate_assets


class StoreAssetTests(unittest.TestCase):
    def test_qualified_assets_match_their_pixel_sizes(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            generate_assets(Image.new('RGBA', (64, 64), 'red'), root)
            for name, size in [('Square44x44Logo.scale-200.png',88),
                               ('Square44x44Logo.scale-400.png',176),
                               ('Square150x150Logo.scale-200.png',300),
                               ('Square44x44Logo.targetsize-256_altform-unplated.png',256)]:
                with Image.open(root / name) as image:
                    self.assertEqual(image.size, (size, size))
                    self.assertEqual(image.getchannel('A').getbbox(), (0, 0, size, size))
    def test_square_icon_is_not_artificially_shrunk(self):
        with tempfile.TemporaryDirectory() as work:
            dest = Path(work) / 'icon.png'
            _asset(Image.new('RGBA', (1024, 1024), 'red'), 44, 44, dest)
            with Image.open(dest) as image:
                self.assertEqual(image.getchannel('A').getbbox(), (0, 0, 44, 44))

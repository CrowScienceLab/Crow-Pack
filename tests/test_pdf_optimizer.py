"""PDF preset optimization regression tests."""

import os
import shutil
import unittest

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

from src.engine.pdf_optimizer import PdfOptimizer


class TestPdfOptimizer(unittest.TestCase):
    qt_app = None

    def setUp(self):
        self.workspace = os.path.abspath("tests/workspace_pdf_optimizer")
        os.makedirs(self.workspace, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_lossless_stream_compression_and_reopen(self):
        source = os.path.join(self.workspace, "source.pdf")
        output = os.path.join(self.workspace, "optimized.pdf")
        writer = PdfWriter()
        page = writer.add_blank_page(width=300, height=300)
        stream = DecodedStreamObject()
        stream.set_data((b"q 0 0 100 100 re S Q\n" * 20_000))
        page[NameObject("/Contents")] = writer._add_object(stream)
        writer.write(source)

        result = PdfOptimizer.optimize(source, output)

        self.assertTrue(result["success"])
        self.assertEqual(result["output_path"], output, result)
        self.assertLess(os.path.getsize(output), os.path.getsize(source))
        verified = PdfReader(output, strict=True)
        self.assertEqual(len(verified.pages), 1)
        self.assertEqual(float(verified.pages[0].mediabox.width), 300.0)

    def test_refuses_to_overwrite_source(self):
        source = os.path.join(self.workspace, "same.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(source)
        with self.assertRaises(ValueError):
            PdfOptimizer.optimize(source, source)

    def test_balanced_preset_recompresses_large_photo(self):
        source = os.path.join(self.workspace, "photo_source.pdf")
        output = os.path.join(self.workspace, "photo_balanced.pdf")
        photo = Image.effect_noise((2400, 1800), 70).convert("RGB")
        photo.save(source, "PDF", quality=100, resolution=300)

        result = PdfOptimizer.optimize(source, output, preset="balanced")

        self.assertTrue(result["success"])
        self.assertEqual(result["output_path"], output, result)
        self.assertGreaterEqual(result["images_processed"], 1)
        self.assertLess(os.path.getsize(output), os.path.getsize(source))
        verified = PdfReader(output, strict=True)
        self.assertEqual(len(verified.pages), 1)

    def test_photo_presets_produce_distinct_monotonic_sizes(self):
        source = os.path.join(self.workspace, "photo_profiles.pdf")
        photo = Image.effect_noise((2800, 2100), 70).convert("RGB")
        photo.save(source, "PDF", quality=100, resolution=300)
        sizes = {}
        for preset in ("high", "balanced", "compact"):
            output = os.path.join(self.workspace, f"photo_{preset}.pdf")
            result = PdfOptimizer.optimize(source, output, preset=preset)
            self.assertTrue(result["success"])
            self.assertGreaterEqual(result["images_processed"], 1)
            sizes[preset] = result["optimized_size"]
        self.assertGreater(sizes["high"], sizes["balanced"])
        self.assertGreater(sizes["balanced"], sizes["compact"])

    def test_low_colour_graphic_is_not_silently_skipped(self):
        source = os.path.join(self.workspace, "low_colour.pdf")
        output = os.path.join(self.workspace, "low_colour_compact.pdf")
        graphic = Image.new("RGB", (2400, 1800), "white")
        for x in range(0, 2400, 40):
            for y in range(0, 1800, 40):
                graphic.paste("black", (x, y, x + 8, y + 8))
        graphic.save(source, "PDF", quality=100, resolution=300)
        result = PdfOptimizer.optimize(source, output, preset="compact")
        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["images_processed"], 1)

    def test_analysis_returns_composition_and_recommendation(self):
        source = os.path.join(self.workspace, "analysis.pdf")
        Image.effect_noise((1600, 1200), 50).convert("RGB").save(source, "PDF", quality=95)
        result = PdfOptimizer.analyze(source)
        self.assertEqual(result["page_count"], 1)
        self.assertGreaterEqual(result["image_count"], 1)
        self.assertIn(result["recommendation"], PdfOptimizer.PRESETS)
        self.assertTrue(result["privacy_local"])

    def test_extreme_preset_rasterizes_locally_and_reduces_photo_pdf(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication

        TestPdfOptimizer.qt_app = QApplication.instance() or QApplication([])
        source = os.path.join(self.workspace, "extreme_source.pdf")
        output = os.path.join(self.workspace, "extreme_output.pdf")
        Image.effect_noise((2400, 1800), 55).convert("RGB").save(source, "PDF", quality=100, resolution=300)
        result = PdfOptimizer.optimize(source, output, preset="extreme")
        self.assertTrue(result["success"])
        self.assertEqual(result["pages_rasterized"], 1)
        self.assertFalse(result["searchable_text"])
        self.assertGreater(result["compression_ratio"], 50)
        self.assertLess(os.path.getsize(output), os.path.getsize(source))


if __name__ == "__main__":
    unittest.main()

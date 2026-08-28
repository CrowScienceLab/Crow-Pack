"""PDF lossless optimization regression tests."""

import os
import shutil
import unittest

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

from src.engine.pdf_optimizer import PdfOptimizer


class TestPdfOptimizer(unittest.TestCase):
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
        self.assertEqual(result["output_path"], output)
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


if __name__ == "__main__":
    unittest.main()

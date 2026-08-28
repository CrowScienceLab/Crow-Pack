"""Lossless structural optimization for PDF documents."""

from __future__ import annotations

import os
import tempfile
from typing import Any, Dict


class PdfOptimizer:
    """Recompress PDF content streams without resampling images or removing content."""

    MAX_INPUT_SIZE = 2 * 1024**3

    @staticmethod
    def _has_digital_signature(reader) -> bool:
        root = reader.trailer.get("/Root", {})
        if root.get("/Perms"):
            return True
        for field in (reader.get_fields() or {}).values():
            if field.get("/FT") == "/Sig" and field.get("/V"):
                return True
        return False

    @classmethod
    def optimize(cls, input_path: str, output_path: str) -> Dict[str, Any]:
        from pypdf import PdfReader, PdfWriter

        source = os.path.abspath(input_path)
        destination = os.path.abspath(output_path)
        if not os.path.isfile(source):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {input_path}")
        if not source.lower().endswith(".pdf"):
            raise ValueError("PDF 파일만 무손실 최적화할 수 있습니다.")
        if os.path.normcase(source) == os.path.normcase(destination):
            raise ValueError("원본 보호를 위해 다른 출력 파일명을 선택하세요.")
        if os.path.exists(destination):
            raise FileExistsError("기존 파일 보호를 위해 출력 PDF를 덮어쓰지 않았습니다.")

        original_size = os.path.getsize(source)
        if original_size > cls.MAX_INPUT_SIZE:
            raise ValueError("2 GiB를 초과하는 PDF는 안전을 위해 최적화하지 않습니다.")

        reader = PdfReader(source, strict=True)
        if reader.is_encrypted:
            raise PermissionError("암호화된 PDF는 무손실 최적화를 지원하지 않습니다.")
        if cls._has_digital_signature(reader):
            raise PermissionError("전자서명 보호를 위해 서명된 PDF는 변경하지 않습니다.")

        page_boxes = [
            (float(page.mediabox.width), float(page.mediabox.height))
            for page in reader.pages
        ]
        output_dir = os.path.dirname(destination)
        os.makedirs(output_dir, exist_ok=True)
        temp_path = ""
        try:
            writer = PdfWriter(clone_from=source)
            for page in writer.pages:
                page.compress_content_streams(level=9)
            writer.compress_identical_objects(
                remove_duplicates=True,
                remove_unreferenced=True,
            )

            with tempfile.NamedTemporaryFile(
                suffix=".pdf",
                prefix=".crowpack-pdf-",
                dir=output_dir,
                delete=False,
            ) as temp_file:
                temp_path = temp_file.name
            writer.write(temp_path)

            verified = PdfReader(temp_path, strict=True)
            if verified.is_encrypted or len(verified.pages) != len(reader.pages):
                raise ValueError("최적화 PDF 검증에 실패했습니다.")
            verified_boxes = [
                (float(page.mediabox.width), float(page.mediabox.height))
                for page in verified.pages
            ]
            if verified_boxes != page_boxes:
                raise ValueError("최적화 과정에서 페이지 크기가 변경되어 결과를 폐기했습니다.")

            optimized_size = os.path.getsize(temp_path)
            if optimized_size >= original_size:
                os.remove(temp_path)
                temp_path = ""
                return {
                    "success": True,
                    "output_path": "",
                    "original_size": original_size,
                    "optimized_size": original_size,
                    "saved_bytes": 0,
                    "message": "이미 충분히 최적화된 PDF라 더 작은 파일을 만들지 않았습니다.",
                }

            os.replace(temp_path, destination)
            temp_path = ""
            return {
                "success": True,
                "output_path": destination,
                "original_size": original_size,
                "optimized_size": optimized_size,
                "saved_bytes": original_size - optimized_size,
                "message": "PDF 무손실 최적화가 완료되었습니다.",
            }
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

"""Preset-based structural and image optimization for PDF documents."""

from __future__ import annotations

import os
import tempfile
from typing import Any, Dict


class PdfOptimizer:
    """Optimize PDFs with four user-facing quality presets."""

    MAX_INPUT_SIZE = 2 * 1024**3
    MAX_IMAGE_PIXELS = 40_000_000
    PRESETS = {
        "lossless": {
            "label": "무손실 최적화",
            "max_edge": None,
            "quality": None,
        },
        "high": {
            "label": "고화질",
            "max_edge": 2480,
            "quality": 90,
        },
        "balanced": {
            "label": "균형 (권장)",
            "max_edge": 1600,
            "quality": 80,
        },
        "compact": {
            "label": "최소 용량",
            "max_edge": 1100,
            "quality": 65,
        },
    }

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
    def _optimize_images(cls, writer, profile: Dict[str, Any]) -> tuple[int, int]:
        from PIL import Image

        processed = 0
        skipped = 0
        seen_objects: set[tuple[int, int]] = set()
        max_edge = int(profile["max_edge"])
        quality = int(profile["quality"])

        for page in writer.pages:
            for embedded in list(page.images):
                reference = embedded.indirect_reference
                if reference is None:
                    skipped += 1
                    continue
                key = (id(reference.pdf), reference.idnum)
                if key in seen_objects:
                    continue
                seen_objects.add(key)
                try:
                    image_object = reference.get_object()
                    width = int(image_object.get("/Width", 0) or 0)
                    height = int(image_object.get("/Height", 0) or 0)
                    if width <= 0 or height <= 0 or width * height > cls.MAX_IMAGE_PIXELS:
                        skipped += 1
                        continue

                    source_image = embedded.image
                    if source_image is None or source_image.mode in {"1", "RGBA", "LA"} or "transparency" in source_image.info:
                        skipped += 1
                        continue

                    # Nearest-neighbour sampling preserves source colour variety.
                    # LANCZOS averaging can make a noisy photograph appear to be
                    # a low-colour graphic and incorrectly skip it.
                    sample = source_image.copy()
                    sample.thumbnail((64, 64), Image.Resampling.NEAREST)
                    colors = sample.convert("RGB").getcolors(maxcolors=257)
                    if colors is not None and len(colors) <= 32:
                        skipped += 1
                        continue

                    optimized = source_image.copy()
                    if optimized.mode not in {"L", "RGB"}:
                        optimized = optimized.convert("RGB")
                    if max(optimized.size) > max_edge:
                        scale = max_edge / max(optimized.size)
                        resized = (
                            max(1, round(optimized.width * scale)),
                            max(1, round(optimized.height * scale)),
                        )
                        optimized = optimized.resize(resized, Image.Resampling.LANCZOS)
                    embedded.replace(optimized, quality=quality, optimize=True)
                    processed += 1
                except Exception:
                    skipped += 1

        return processed, skipped

    @classmethod
    def optimize(cls, input_path: str, output_path: str, preset: str = "lossless") -> Dict[str, Any]:
        from pypdf import PdfReader, PdfWriter

        if preset not in cls.PRESETS:
            raise ValueError(f"지원하지 않는 PDF 압축 프리셋입니다: {preset}")
        profile = cls.PRESETS[preset]
        source = os.path.abspath(input_path)
        destination = os.path.abspath(output_path)
        if not os.path.isfile(source):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {input_path}")
        if not source.lower().endswith(".pdf"):
            raise ValueError("PDF 파일만 최적화할 수 있습니다.")
        if os.path.normcase(source) == os.path.normcase(destination):
            raise ValueError("원본 보호를 위해 다른 출력 파일명을 선택하세요.")
        if os.path.exists(destination):
            raise FileExistsError("기존 파일 보호를 위해 출력 PDF를 덮어쓰지 않았습니다.")

        original_size = os.path.getsize(source)
        if original_size > cls.MAX_INPUT_SIZE:
            raise ValueError("2 GiB를 초과하는 PDF는 안전을 위해 최적화하지 않습니다.")

        reader = PdfReader(source, strict=True)
        if reader.is_encrypted:
            raise PermissionError("암호화된 PDF는 최적화를 지원하지 않습니다.")
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
            images_processed = 0
            images_skipped = 0
            if preset != "lossless":
                images_processed, images_skipped = cls._optimize_images(writer, profile)
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
                    "preset": preset,
                    "preset_label": profile["label"],
                    "images_processed": images_processed,
                    "images_skipped": images_skipped,
                    "message": "선택한 품질에서 더 작은 결과를 만들 수 없어 원본을 유지했습니다.",
                }

            os.replace(temp_path, destination)
            temp_path = ""
            return {
                "success": True,
                "output_path": destination,
                "original_size": original_size,
                "optimized_size": optimized_size,
                "saved_bytes": original_size - optimized_size,
                "preset": preset,
                "preset_label": profile["label"],
                "images_processed": images_processed,
                "images_skipped": images_skipped,
                "message": f"PDF {profile['label']} 처리가 완료되었습니다.",
            }
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

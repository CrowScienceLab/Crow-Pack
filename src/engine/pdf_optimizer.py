"""Local-only PDF analysis, structural cleanup, image optimization and raster fallback."""

from __future__ import annotations

import io
import os
import tempfile
from collections import Counter
from typing import Any, Dict


class PdfOptimizer:
    """Optimize PDFs with content-aware presets without uploading user documents."""

    MAX_INPUT_SIZE = 2 * 1024**3
    MAX_IMAGE_PIXELS = 80_000_000
    MAX_RENDER_PIXELS = 24_000_000
    PRESETS = {
        "lossless": {"label": "무손실 정리", "max_edge": None, "quality": None, "target_dpi": None, "rasterize": False},
        "high": {"label": "문서 최적화", "max_edge": 2480, "quality": 90, "target_dpi": 240, "rasterize": False},
        "balanced": {"label": "균형 압축 (권장)", "max_edge": 1600, "quality": 78, "target_dpi": 160, "rasterize": False},
        "compact": {"label": "최소 용량", "max_edge": 1100, "quality": 58, "target_dpi": 110, "rasterize": False},
        "extreme": {"label": "극한 압축", "max_edge": None, "quality": 50, "target_dpi": 120, "rasterize": True},
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

    @staticmethod
    def _stream_size(stream) -> int:
        if stream is None:
            return 0
        try:
            return len(stream.get_data())
        except Exception:
            return 0

    @classmethod
    def analyze(cls, input_path: str) -> Dict[str, Any]:
        """Return a conservative local size profile used for recommendations and reporting."""
        from pypdf import PdfReader

        source = os.path.abspath(input_path)
        if not os.path.isfile(source):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {input_path}")
        if not source.lower().endswith(".pdf"):
            raise ValueError("PDF 파일만 분석할 수 있습니다.")
        original_size = os.path.getsize(source)
        if original_size > cls.MAX_INPUT_SIZE:
            raise ValueError("2 GiB를 초과하는 PDF는 안전을 위해 처리하지 않습니다.")

        reader = PdfReader(source, strict=True)
        if reader.is_encrypted:
            return {
                "input_path": source, "filename": os.path.basename(source), "original_size": original_size,
                "page_count": 0, "encrypted": True, "signed": False, "document_type": "encrypted",
                "recommendation": "none", "recommendation_label": "처리 불가", "image_count": 0,
                "image_bytes": 0, "font_bytes": 0, "attachment_bytes": 0, "other_bytes": original_size,
                "composition": {"images": 0.0, "fonts": 0.0, "attachments": 0.0, "other": 100.0},
                "privacy_local": True,
            }

        image_bytes = 0
        image_count = 0
        font_bytes = 0
        seen_images: set[tuple[int, int]] = set()
        seen_fonts: set[tuple[int, int]] = set()
        for page in reader.pages:
            for embedded in list(page.images):
                reference = embedded.indirect_reference
                key = (id(reference.pdf), reference.idnum) if reference is not None else (id(embedded), 0)
                if key in seen_images:
                    continue
                seen_images.add(key)
                image_count += 1
                image_bytes += len(embedded.data or b"")

            resources = page.get("/Resources") or {}
            fonts = resources.get("/Font") or {}
            for font_reference in fonts.values():
                reference = getattr(font_reference, "indirect_reference", None)
                key = (id(reference.pdf), reference.idnum) if reference is not None else (id(font_reference), 0)
                if key in seen_fonts:
                    continue
                seen_fonts.add(key)
                try:
                    font = font_reference.get_object()
                    descriptor = font.get("/FontDescriptor")
                    if descriptor:
                        descriptor = descriptor.get_object()
                        for font_file_name in ("/FontFile", "/FontFile2", "/FontFile3"):
                            font_bytes += cls._stream_size(descriptor.get(font_file_name))
                except Exception:
                    pass

        attachment_bytes = 0
        try:
            for name in reader.attachments:
                payloads = reader.attachments[name]
                if not isinstance(payloads, list):
                    payloads = [payloads]
                attachment_bytes += sum(len(payload) for payload in payloads if isinstance(payload, bytes))
        except Exception:
            attachment_bytes = 0

        accounted = min(original_size, image_bytes + font_bytes + attachment_bytes)
        other_bytes = max(0, original_size - accounted)
        denominator = max(1, original_size)
        composition = {
            "images": round(min(image_bytes, original_size) * 100 / denominator, 1),
            "fonts": round(min(font_bytes, original_size) * 100 / denominator, 1),
            "attachments": round(min(attachment_bytes, original_size) * 100 / denominator, 1),
            "other": round(other_bytes * 100 / denominator, 1),
        }
        if image_count and composition["images"] >= 45:
            document_type = "scan_or_photo"
            recommendation = "balanced" if original_size < 30 * 1024**2 else "compact"
        elif font_bytes >= original_size * 0.12:
            document_type = "office_document"
            recommendation = "high"
        else:
            document_type = "text_or_vector"
            recommendation = "lossless"

        return {
            "input_path": source, "filename": os.path.basename(source), "original_size": original_size,
            "page_count": len(reader.pages), "encrypted": False, "signed": cls._has_digital_signature(reader),
            "document_type": document_type, "recommendation": recommendation,
            "recommendation_label": cls.PRESETS[recommendation]["label"], "image_count": image_count,
            "image_bytes": image_bytes, "font_bytes": font_bytes, "attachment_bytes": attachment_bytes,
            "other_bytes": other_bytes, "composition": composition, "privacy_local": True,
        }

    @classmethod
    def _optimize_images(cls, writer, profile: Dict[str, Any]) -> tuple[int, int, Dict[str, int]]:
        from PIL import Image

        processed = 0
        skipped = 0
        reasons: Counter[str] = Counter()
        seen_objects: set[tuple[int, int]] = set()
        max_edge = int(profile["max_edge"])
        quality = int(profile["quality"])
        for page in writer.pages:
            for embedded in list(page.images):
                reference = embedded.indirect_reference
                if reference is None:
                    skipped += 1
                    reasons["인라인 이미지"] += 1
                    continue
                key = (id(reference.pdf), reference.idnum)
                if key in seen_objects:
                    continue
                seen_objects.add(key)
                try:
                    image_object = reference.get_object()
                    width = int(image_object.get("/Width", 0) or 0)
                    height = int(image_object.get("/Height", 0) or 0)
                    if width <= 0 or height <= 0:
                        skipped += 1
                        reasons["크기 정보 없음"] += 1
                        continue
                    if width * height > cls.MAX_IMAGE_PIXELS:
                        skipped += 1
                        reasons["안전 한도 초과 대형 이미지"] += 1
                        continue
                    source_image = embedded.image
                    if source_image is None:
                        skipped += 1
                        reasons["이미지 해석 실패"] += 1
                        continue
                    if source_image.mode in {"RGBA", "LA"} or "transparency" in source_image.info:
                        rgba = source_image.convert("RGBA")
                        optimized = Image.new("RGB", rgba.size, "white")
                        optimized.paste(rgba.convert("RGB"), mask=rgba.getchannel("A"))
                    elif source_image.mode == "1":
                        optimized = source_image.convert("L")
                    elif source_image.mode not in {"L", "RGB"}:
                        optimized = source_image.convert("RGB")
                    else:
                        optimized = source_image.copy()
                    if max(optimized.size) > max_edge:
                        scale = max_edge / max(optimized.size)
                        optimized = optimized.resize(
                            (max(1, round(optimized.width * scale)), max(1, round(optimized.height * scale))),
                            Image.Resampling.LANCZOS,
                        )
                    embedded.replace(optimized, quality=quality, optimize=True)
                    processed += 1
                except Exception as exc:
                    skipped += 1
                    reasons[f"처리 오류({type(exc).__name__})"] += 1
        return processed, skipped, dict(reasons)

    @classmethod
    def _rasterize_document(cls, source: str, destination: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Render every visible page locally, discarding interactive PDF structures."""
        from PIL import Image, ImageStat
        from pypdf import PdfWriter
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize
        from PySide6.QtPdf import QPdfDocument

        document = QPdfDocument()
        load_error = document.load(source)
        if load_error != QPdfDocument.Error.None_:
            raise ValueError(f"PDF 페이지 렌더링을 시작할 수 없습니다: {load_error}")
        if document.pageCount() <= 0:
            raise ValueError("렌더링할 PDF 페이지가 없습니다.")

        target_dpi = int(profile["target_dpi"])
        quality = int(profile["quality"])
        mode_counts: Counter[str] = Counter()
        with tempfile.TemporaryDirectory(prefix=".crowpack-raster-", dir=os.path.dirname(destination)) as work_dir:
            page_pdfs = []
            for page_number in range(document.pageCount()):
                point_size = document.pagePointSize(page_number)
                width = max(1, round(point_size.width() * target_dpi / 72))
                height = max(1, round(point_size.height() * target_dpi / 72))
                pixels = width * height
                if pixels > cls.MAX_RENDER_PIXELS:
                    scale = (cls.MAX_RENDER_PIXELS / pixels) ** 0.5
                    width = max(1, round(width * scale))
                    height = max(1, round(height * scale))
                rendered = document.render(page_number, QSize(width, height))
                if rendered.isNull():
                    raise ValueError(f"{page_number + 1}페이지 렌더링에 실패했습니다.")
                data = QByteArray()
                buffer = QBuffer(data)
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                if not rendered.save(buffer, "PNG"):
                    raise ValueError(f"{page_number + 1}페이지 이미지 변환에 실패했습니다.")
                buffer.close()
                with Image.open(io.BytesIO(bytes(data))) as opened:
                    page_image = opened.convert("RGB")
                sample = page_image.copy()
                sample.thumbnail((128, 128), Image.Resampling.BILINEAR)
                stats = ImageStat.Stat(sample)
                channel_spread = max(stats.mean) - min(stats.mean)
                colors = sample.getcolors(maxcolors=257)
                if colors is not None and len(colors) <= 8:
                    encoded = page_image.convert("L").point(lambda value: 255 if value > 190 else 0, mode="1")
                    mode_name = "monochrome"
                elif channel_spread < 3:
                    encoded = page_image.convert("L")
                    mode_name = "grayscale"
                else:
                    encoded = page_image
                    mode_name = "color"
                mode_counts[mode_name] += 1
                page_path = os.path.join(work_dir, f"page-{page_number:06d}.pdf")
                save_args: Dict[str, Any] = {"resolution": target_dpi}
                if encoded.mode != "1":
                    save_args.update({"quality": quality, "optimize": True})
                encoded.save(page_path, "PDF", **save_args)
                page_pdfs.append(page_path)
            writer = PdfWriter()
            for page_path in page_pdfs:
                writer.append(page_path)
            writer.metadata = None
            writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
            writer.write(destination)
        document.close()
        return {
            "pages_rasterized": sum(mode_counts.values()), "render_modes": dict(mode_counts),
            "target_dpi": target_dpi, "searchable_text": False,
            "removed_features": ["전자서명", "링크", "양식", "주석", "레이어", "원본 텍스트 구조"],
        }

    @classmethod
    def optimize(cls, input_path: str, output_path: str, preset: str = "lossless") -> Dict[str, Any]:
        from pypdf import PdfReader, PdfWriter

        if preset not in cls.PRESETS:
            raise ValueError(f"지원하지 않는 PDF 압축 프리셋입니다: {preset}")
        profile = cls.PRESETS[preset]
        analysis = cls.analyze(input_path)
        source = analysis["input_path"]
        destination = os.path.abspath(output_path)
        if analysis["encrypted"]:
            raise PermissionError("암호화된 PDF는 최적화를 지원하지 않습니다.")
        if analysis["signed"]:
            raise PermissionError("전자서명 보호를 위해 서명된 PDF는 변경하지 않습니다.")
        if os.path.normcase(source) == os.path.normcase(destination):
            raise ValueError("원본 보호를 위해 다른 출력 파일명을 선택하세요.")
        if os.path.exists(destination):
            raise FileExistsError("기존 파일 보호를 위해 출력 PDF를 덮어쓰지 않았습니다.")

        reader = PdfReader(source, strict=True)
        page_boxes = [(float(page.mediabox.width), float(page.mediabox.height)) for page in reader.pages]
        original_size = analysis["original_size"]
        output_dir = os.path.dirname(destination)
        os.makedirs(output_dir, exist_ok=True)
        temp_path = ""
        images_processed = 0
        images_skipped = 0
        skip_reasons: Dict[str, int] = {}
        raster_report: Dict[str, Any] = {}
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", prefix=".crowpack-pdf-", dir=output_dir, delete=False) as temp_file:
                temp_path = temp_file.name
            if profile["rasterize"]:
                raster_report = cls._rasterize_document(source, temp_path, profile)
            else:
                writer = PdfWriter(clone_from=source)
                if preset != "lossless":
                    images_processed, images_skipped, skip_reasons = cls._optimize_images(writer, profile)
                    writer.metadata = None
                for page in writer.pages:
                    page.compress_content_streams(level=9)
                writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
                writer.write(temp_path)

            verified = PdfReader(temp_path, strict=True)
            if verified.is_encrypted or len(verified.pages) != len(reader.pages):
                raise ValueError("최적화 PDF 검증에 실패했습니다.")
            if not profile["rasterize"]:
                verified_boxes = [(float(page.mediabox.width), float(page.mediabox.height)) for page in verified.pages]
                if verified_boxes != page_boxes:
                    raise ValueError("최적화 과정에서 페이지 크기가 변경되어 결과를 폐기했습니다.")

            optimized_size = os.path.getsize(temp_path)
            common = {
                "success": True, "original_size": original_size, "preset": preset,
                "preset_label": profile["label"], "images_processed": images_processed,
                "images_skipped": images_skipped, "skip_reasons": skip_reasons, "analysis": analysis,
                "privacy_local": True, "searchable_text": raster_report.get("searchable_text", True), **raster_report,
            }
            if optimized_size >= original_size:
                os.remove(temp_path)
                temp_path = ""
                return {
                    **common, "output_path": "", "optimized_size": original_size, "saved_bytes": 0,
                    "compression_ratio": 0.0,
                    "message": "선택한 품질에서 더 작은 결과를 만들 수 없어 원본을 유지했습니다.",
                }
            os.replace(temp_path, destination)
            temp_path = ""
            saved_bytes = original_size - optimized_size
            return {
                **common, "output_path": destination, "optimized_size": optimized_size,
                "saved_bytes": saved_bytes, "compression_ratio": round(saved_bytes * 100 / max(1, original_size), 1),
                "message": f"PDF {profile['label']} 처리가 완료되었습니다.",
            }
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

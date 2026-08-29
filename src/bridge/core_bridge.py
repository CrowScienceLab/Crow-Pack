"""
Crow Pack - PySide6 WebChannel Core Bridge
UI와 파이썬 아카이브 엔진 간의 네이티브 양방향 브릿지 (Crow Pack v1.0K)
"""

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import winreg

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, Qt, Signal, Slot
from PySide6.QtGui import QImageReader
from PySide6.QtWidgets import QFileDialog

from ..engine.archive_manager import ArchiveManager
from ..engine.pdf_optimizer import PdfOptimizer


class CoreBridge(QObject):
    """JavaScript와 통신하는 핵심 네이티브 브릿지 클래스"""

    _BLOCKED_PREVIEW_EXTENSIONS = {
        ".bat", ".cmd", ".com", ".cpl", ".exe", ".hta", ".js", ".jse",
        ".lnk", ".msi", ".ps1", ".reg", ".scr", ".url", ".vbs", ".wsf", ".wsh",
    }
    _IMAGE_PREVIEW_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
    _MAX_IMAGE_PREVIEW_BYTES = 20 * 1024**2
    _MAX_IMAGE_PREVIEW_PIXELS = 40_000_000
    APP_VERSION = "1.0K"
    RELEASE_TAG = "v1.0K"
    LATEST_RELEASE_API = "https://api.github.com/repos/CrowScienceLab/Crow-Pack/releases/latest"
    
    progressEvent = Signal(int, int, str)

    def __init__(self, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget

    @Slot(result=str)
    def selectArchiveFile(self) -> str:
        """압축 파일 선택 다이얼로그"""
        filter_str = (
            "모든 지원 파일 (*.zip *.alz *.egg *.7z *.rar *.tar *.tar.gz *.tgz *.tar.bz2 *.tbz2 *.tar.xz *.txz *.cab *.iso);;"
            "ZIP 아카이브 (*.zip);;"
            "알집 ALZ / EGG (*.alz *.egg);;"
            "7-Zip 아카이브 (*.7z);;"
            "WinRAR 아카이브 (*.rar);;"
            "TAR 아카이브 (*.tar *.tar.gz *.tar.bz2 *.tar.xz);;"
            "ISO 디스크 이미지 (*.iso);;"
            "모든 파일 (*.*)"
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent_widget,
            "압축 파일 열기 - Crow Pack",
            "",
            filter_str
        )
        return file_path or ""

    @Slot(result=str)
    def selectIsoFile(self) -> str:
        """읽기 전용으로 탐색할 ISO 이미지 선택 다이얼로그"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent_widget,
            "ISO 이미지 열기 - Crow Pack",
            "",
            "ISO 디스크 이미지 (*.iso);;모든 파일 (*.*)",
        )
        return file_path or ""

    @Slot(result=str)
    def selectSourceFiles(self) -> str:
        """압축할 파일들 다중 선택 다이얼로그"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.parent_widget,
            "압축할 파일 추가 - Crow Pack",
            "",
            "모든 파일 (*.*)"
        )
        return json.dumps(file_paths or [])

    @Slot(result=str)
    def selectSourceFolder(self) -> str:
        """압축할 폴더 선택 다이얼로그"""
        folder_path = QFileDialog.getExistingDirectory(
            self.parent_widget,
            "압축할 폴더 추가 - Crow Pack",
            ""
        )
        if folder_path:
            return json.dumps([folder_path])
        return json.dumps([])

    @Slot(str, result=str)
    def getFilesDetails(self, paths_json: str) -> str:
        """드롭/선택된 파일/폴더 경로들의 총 파일 개수 및 총 바이트 크기 계산"""
        try:
            paths = json.loads(paths_json)
            total_size = 0
            file_count = 0
            details = []

            for p in paths:
                if not os.path.exists(p):
                    continue
                if os.path.isfile(p):
                    sz = os.path.getsize(p)
                    total_size += sz
                    file_count += 1
                    details.append({"name": os.path.basename(p), "path": p, "size": sz, "is_dir": False})
                elif os.path.isdir(p):
                    dir_sz = 0
                    dir_files = 0
                    for root, _, files in os.walk(p):
                        for f in files:
                            fp = os.path.join(root, f)
                            sz = os.path.getsize(fp)
                            dir_sz += sz
                            dir_files += 1
                    total_size += dir_sz
                    file_count += dir_files
                    details.append({"name": os.path.basename(p), "path": p, "size": dir_sz, "is_dir": True, "file_count": dir_files})

            return json.dumps({
                "success": True,
                "file_count": file_count,
                "total_size": total_size,
                "items": details
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(str, str, str, result=str)
    def listArchive(self, file_path: str, password: str = "", encoding: str = "") -> str:
        """압축 파일 내부 상세 목록 조회"""
        try:
            pwd = password if password.strip() else None
            enc = encoding if encoding.strip() else None
            info = ArchiveManager.list_archive(file_path, password=pwd, encoding=enc)
            return json.dumps(info, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @Slot(str, str, result=str)
    def testArchive(self, file_path: str, password: str = "") -> str:
        """아카이브 무결성 검사"""
        try:
            pwd = password if password.strip() else None
            is_valid, err_msg = ArchiveManager.test_archive(file_path, password=pwd)
            return json.dumps({
                "success": is_valid,
                "error": err_msg
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(str, str, str, result=str)
    def extractSingleAndOpen(self, file_path: str, item_name: str, password: str = "") -> str:
        """더블클릭 실행"""
        try:
            extension = os.path.splitext(item_name.rstrip("/\\"))[1].lower()
            if extension in self._BLOCKED_PREVIEW_EXTENSIONS:
                raise PermissionError(
                    "실행 가능한 파일은 보안상 아카이브에서 바로 열 수 없습니다. 먼저 별도 폴더에 해제한 뒤 확인하세요."
                )
            pwd = password if password.strip() else None
            temp_file = ArchiveManager.extract_single_temp(file_path, item_name, password=pwd)
            os.startfile(temp_file)
            return json.dumps({"success": True, "temp_file": temp_file}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(str, str, str, result=str)
    def getImagePreview(self, file_path: str, item_name: str, password: str = "") -> str:
        """아카이브 항목을 제한된 크기의 PNG 썸네일로 변환"""
        temp_file = ""
        try:
            extension = os.path.splitext(item_name.rstrip("/\\"))[1].lower()
            if extension not in self._IMAGE_PREVIEW_EXTENSIONS:
                raise ValueError("미리보기를 지원하는 그림 형식이 아닙니다.")
            pwd = password if password.strip() else None
            temp_file = ArchiveManager.extract_single_temp(file_path, item_name, password=pwd)
            file_size = os.path.getsize(temp_file)
            if file_size > self._MAX_IMAGE_PREVIEW_BYTES:
                raise ValueError("20 MiB를 초과하는 그림은 안전을 위해 미리보지 않습니다.")

            reader = QImageReader(temp_file)
            reader.setAutoTransform(True)
            image_size = reader.size()
            if not image_size.isValid():
                raise ValueError("그림 파일의 크기를 확인할 수 없습니다.")
            if image_size.width() * image_size.height() > self._MAX_IMAGE_PREVIEW_PIXELS:
                raise ValueError("4천만 픽셀을 초과하는 그림은 안전을 위해 미리보지 않습니다.")
            if image_size.width() > 720 or image_size.height() > 480:
                image_size.scale(720, 480, Qt.KeepAspectRatio)
                reader.setScaledSize(image_size)

            image = reader.read()
            if image.isNull():
                raise ValueError(reader.errorString() or "그림을 읽을 수 없습니다.")
            encoded = QByteArray()
            buffer = QBuffer(encoded)
            buffer.open(QIODevice.WriteOnly)
            if not image.save(buffer, "PNG"):
                raise ValueError("미리보기 이미지를 만들 수 없습니다.")
            data_url = "data:image/png;base64," + bytes(encoded.toBase64()).decode("ascii")
            return json.dumps({
                "success": True,
                "name": os.path.basename(item_name),
                "data_url": data_url,
                "width": image.width(),
                "height": image.height(),
                "size": file_size,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
        finally:
            if temp_file:
                preview_dir = os.path.dirname(temp_file)
                if os.path.basename(preview_dir).startswith("crow_pack_preview_"):
                    shutil.rmtree(preview_dir, ignore_errors=True)
                elif os.path.isfile(temp_file):
                    os.remove(temp_file)

    @Slot(str, str, bool, result=str)
    def exportArchiveItems(self, file_path: str, items_json: str, move_after_copy: bool = False) -> str:
        """선택 항목을 폴더로 복사하고, ZIP에 한해 원본 항목을 선택적으로 삭제"""
        try:
            items = json.loads(items_json)
            if not items:
                raise ValueError("복사할 항목이 없습니다.")
            archive_format = ArchiveManager.detect_format(file_path)
            if move_after_copy and archive_format != "ZIP":
                raise PermissionError("파일 이동은 수정 가능한 ZIP에서만 지원합니다. ISO와 기타 형식은 복사만 가능합니다.")
            destination = QFileDialog.getExistingDirectory(
                self.parent_widget,
                "파일을 복사할 대상 폴더 선택 - Crow Pack",
                os.path.dirname(os.path.abspath(file_path)),
            )
            if not destination:
                return json.dumps({"success": False, "cancelled": True}, ensure_ascii=False)

            def on_progress(cur, tot, fn):
                self.progressEvent.emit(cur, tot, fn)

            output_dir, extracted = ArchiveManager.extract_archive(
                file_path,
                destination,
                mode="current",
                selected_files=items,
                progress_callback=on_progress,
            )
            if move_after_copy:
                ArchiveManager.delete_files(file_path, items)
            return json.dumps({
                "success": True,
                "dest_dir": output_dir,
                "copied_count": len(extracted),
                "moved": move_after_copy,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(str, str, bool, str, str, result=str)
    def extractArchiveWithOption(self, file_path: str, mode: str = "smart", use_default_dir: bool = True,
                                 selected_files_json: str = "", password: str = "") -> str:
        """
        압축 해제 실행
        - use_default_dir = True : '이 폴더에 풀기' (아카이브 위치)
        - use_default_dir = False: '폴더변경 풀기' (사용자 선택 폴더)
        """
        try:
            pwd = password if password.strip() else None
            selected_files = json.loads(selected_files_json) if selected_files_json.strip() else None

            if use_default_dir:
                dest_base = os.path.dirname(os.path.abspath(file_path))
            else:
                dest_base = QFileDialog.getExistingDirectory(
                    self.parent_widget,
                    "압축 해제할 대상 폴더 선택 - Crow Pack",
                    os.path.dirname(os.path.abspath(file_path))
                )
                if not dest_base:
                    return json.dumps({"success": False, "error": "해제 폴더 선택이 취소되었습니다."}, ensure_ascii=False)

            def on_progress(cur, tot, fn):
                self.progressEvent.emit(cur, tot, fn)

            dest_dir, extracted_files = ArchiveManager.extract_archive(
                file_path,
                dest_base,
                mode=mode,
                selected_files=selected_files,
                password=pwd,
                progress_callback=on_progress
            )

            return json.dumps({
                "success": True,
                "dest_dir": dest_dir,
                "extracted_count": len(extracted_files)
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(str, str, str, int, str, int, bool, result=str)
    def createArchiveWithOption(self, paths_json: str, format_type: str = "ZIP", preset: str = "windows",
                                level: int = 6, password: str = "", split_size_mb: int = 0,
                                change_folder: bool = False) -> str:
        """
        신규 압축 파일 생성
        - change_folder = False: '이 폴더에 압축' (소스 파일 위치에 바로 저장)
        - change_folder = True : '폴더변경 압축' (사용자가 저장 경로/이름 직접 지정)
        """
        try:
            file_paths = json.loads(paths_json)
            if not file_paths:
                return json.dumps({"success": False, "error": "압축할 파일이 없습니다."}, ensure_ascii=False)

            first_path = file_paths[0]
            base_dir = os.path.dirname(os.path.abspath(first_path))
            base_name = os.path.splitext(os.path.basename(first_path))[0]
            
            ext_map = {
                "ZIP": ".zip",
                "7Z": ".7z",
                "TAR.GZ": ".tar.gz",
                "TAR.XZ": ".tar.xz",
                "TAR.BZ2": ".tar.bz2",
                "TAR": ".tar"
            }
            ext = ext_map.get(format_type.upper(), ".zip")
            default_out = os.path.join(base_dir, f"{base_name}{ext}")

            if change_folder:
                save_path, _ = QFileDialog.getSaveFileName(
                    self.parent_widget,
                    "압축 파일 저장 위치 지정 - Crow Pack",
                    default_out,
                    f"{format_type} 파일 (*{ext});;모든 파일 (*.*)"
                )
                if not save_path:
                    return json.dumps({"success": False, "error": "압축 저장이 취소되었습니다."}, ensure_ascii=False)
            else:
                save_path = default_out

            if os.path.exists(save_path):
                return json.dumps({
                    "success": False,
                    "error": "같은 이름의 파일이 이미 있습니다. 기존 파일 보호를 위해 덮어쓰지 않았습니다."
                }, ensure_ascii=False)

            pwd = password if password.strip() else None

            def on_progress(cur, tot, fn):
                self.progressEvent.emit(cur, tot, fn)

            out_file = ArchiveManager.create_archive(
                file_paths,
                save_path,
                format_type=format_type,
                preset=preset,
                level=level,
                password=pwd,
                split_size_mb=split_size_mb,
                progress_callback=on_progress
            )

            return json.dumps({
                "success": True,
                "output_path": out_file,
                "output_dir": os.path.dirname(out_file)
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(str, str, result=str)
    def addFilesToArchive(self, archive_path: str, paths_json: str) -> str:
        """기존 아카이브에 파일 추가"""
        try:
            paths = json.loads(paths_json)
            ArchiveManager.add_files(archive_path, paths)
            return json.dumps({"success": True}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(str, str, result=str)
    def deleteFilesFromArchive(self, archive_path: str, items_json: str) -> str:
        """기존 아카이브에서 파일 삭제"""
        try:
            items = json.loads(items_json)
            ArchiveManager.delete_files(archive_path, items)
            return json.dumps({"success": True}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(str, str, result=str)
    def createIsoImage(self, paths_json: str, volume_label: str = "CROW_PACK") -> str:
        """선택한 파일과 폴더로 Joliet/Rock Ridge 데이터 ISO 생성"""
        try:
            paths = json.loads(paths_json)
            if not paths:
                raise ValueError("ISO에 넣을 파일이나 폴더가 없습니다.")
            first_path = os.path.abspath(paths[0])
            first_name = os.path.basename(first_path.rstrip("\\/"))
            stem = os.path.splitext(first_name)[0] or "CrowPack_Data"
            default_output = os.path.join(os.path.dirname(first_path), f"{stem}.iso")
            output_path, _ = QFileDialog.getSaveFileName(
                self.parent_widget,
                "ISO 이미지 저장 위치 - Crow Pack",
                default_output,
                "ISO 디스크 이미지 (*.iso)",
            )
            if not output_path:
                return json.dumps({"success": False, "cancelled": True}, ensure_ascii=False)

            def on_progress(cur, tot, filename):
                self.progressEvent.emit(cur, tot, filename)

            output = ArchiveManager.create_iso(
                paths,
                output_path,
                volume_label=volume_label.strip() or "CROW_PACK",
                progress_callback=on_progress,
            )
            return json.dumps({
                "success": True,
                "output_path": output,
                "output_dir": os.path.dirname(output),
                "size": os.path.getsize(output),
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(result=str)
    def optimizePdf(self) -> str:
        """기존 호출 호환용 무손실 PDF 최적화"""
        return self._optimize_pdf("lossless")

    @Slot(str, result=str)
    def optimizePdfPreset(self, preset: str) -> str:
        """선택한 품질 프리셋으로 PDF 최적화"""
        return self._optimize_pdf(preset)

    def _optimize_pdf(self, preset: str) -> str:
        try:
            profile = PdfOptimizer.PRESETS.get(preset)
            if profile is None:
                raise ValueError("지원하지 않는 PDF 압축 프리셋입니다.")
            input_path, _ = QFileDialog.getOpenFileName(
                self.parent_widget,
                f"{profile['label']} 처리할 PDF 선택 - Crow Pack",
                "",
                "PDF 문서 (*.pdf)",
            )
            if not input_path:
                return json.dumps({"success": False, "cancelled": True}, ensure_ascii=False)
            stem, _ = os.path.splitext(input_path)
            suffix = {
                "lossless": "lossless",
                "high": "high",
                "balanced": "balanced",
                "compact": "compact",
            }[preset]
            output_path, _ = QFileDialog.getSaveFileName(
                self.parent_widget,
                "최적화 PDF 저장 위치 - Crow Pack",
                f"{stem}_{suffix}.pdf",
                "PDF 문서 (*.pdf)",
            )
            if not output_path:
                return json.dumps({"success": False, "cancelled": True}, ensure_ascii=False)
            result = PdfOptimizer.optimize(input_path, output_path, preset=preset)
            result["output_dir"] = os.path.dirname(result.get("output_path") or input_path)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(result=str)
    def checkForUpdates(self) -> str:
        """GitHub 최신 릴리스 태그와 현재 버전 비교"""
        try:
            if not self.LATEST_RELEASE_API.startswith("https://api.github.com/"):
                raise ValueError("허용되지 않은 업데이트 주소입니다.")
            request = urllib.request.Request(  # noqa: S310 - fixed HTTPS GitHub API endpoint
                self.LATEST_RELEASE_API,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": f"Crow-Pack/{self.APP_VERSION}",
                },
            )
            with urllib.request.urlopen(request, timeout=8) as response:  # noqa: S310
                release = json.load(response)
            latest_tag = str(release.get("tag_name", "")).strip()
            if not latest_tag:
                raise ValueError("최신 릴리스 태그가 비어 있습니다.")
            update_available = latest_tag.casefold() != self.RELEASE_TAG.casefold()
            message = (
                f"새 릴리스 {latest_tag}을 사용할 수 있습니다."
                if update_available
                else "현재 최신 버전을 사용하고 있습니다."
            )
            return json.dumps({
                "success": True,
                "version": self.APP_VERSION,
                "latest_tag": latest_tag,
                "update_available": update_available,
                "release_url": release.get("html_url", ""),
                "message": message,
            }, ensure_ascii=False)
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            return json.dumps({
                "success": False,
                "version": self.APP_VERSION,
                "update_available": False,
                "error": f"GitHub 릴리스를 확인할 수 없습니다: {e}",
            }, ensure_ascii=False)

    @Slot(result=str)
    def registerFileAssociations(self) -> str:
        """현재 사용자에게 Crow Pack을 연결 후보로 등록하고 기본 앱 설정 열기"""
        try:
            if getattr(sys, "frozen", False):
                open_command = f'"{sys.executable}" "%1"'
                icon_path = sys.executable
            else:
                pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                launcher = pythonw if os.path.exists(pythonw) else sys.executable
                main_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "main.py"))
                open_command = f'"{launcher}" "{main_script}" "%1"'
                icon_path = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "..", "assets", "crow_pack.ico")
                )

            prog_id = "CrowPack.Archive"
            classes_root = r"Software\Classes"
            capabilities = r"Software\Crow Science Lab\Crow Pack\Capabilities"
            extensions = [
                ".7z", ".alz", ".cab", ".egg", ".gz", ".iso", ".rar",
                ".tar", ".tbz2", ".tgz", ".txz", ".xz", ".zip",
            ]
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{classes_root}\\{prog_id}") as key:
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, "Crow Pack Archive")
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{classes_root}\\{prog_id}\\DefaultIcon") as key:
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, f'"{icon_path}",0')
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{classes_root}\\{prog_id}\\shell\\open\\command") as key:
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, open_command)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, capabilities) as key:
                winreg.SetValueEx(key, "ApplicationName", 0, winreg.REG_SZ, "Crow Pack")
                winreg.SetValueEx(key, "ApplicationDescription", 0, winreg.REG_SZ, "압축 파일과 ISO 이미지 탐색")
                winreg.SetValueEx(key, "ApplicationIcon", 0, winreg.REG_SZ, f'"{icon_path}",0')
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{capabilities}\\FileAssociations") as key:
                for extension in extensions:
                    winreg.SetValueEx(key, extension, 0, winreg.REG_SZ, prog_id)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\RegisteredApplications") as key:
                winreg.SetValueEx(key, "Crow Pack", 0, winreg.REG_SZ, capabilities)
            for extension in extensions:
                with winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER,
                    f"{classes_root}\\{extension}\\OpenWithProgids",
                ) as key:
                    winreg.SetValueEx(key, prog_id, 0, winreg.REG_NONE, b"")

            try:
                import ctypes

                ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
            except Exception:
                pass
            os.startfile("ms-settings:defaultapps")
            return json.dumps({
                "success": True,
                "message": "Crow Pack을 연결 후보로 등록했습니다. Windows 기본 앱 화면에서 확장자를 선택하세요.",
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(str)
    def openFolder(self, path: str):
        """지정된 파일 또는 폴더를 윈도우 탐색기에서 열기"""
        if not path:
            return
        abs_path = os.path.abspath(path)
        if os.path.isfile(abs_path):
            subprocess.run(["explorer.exe", f"/select,{abs_path}"], shell=False, check=False)
        elif os.path.isdir(abs_path):
            os.startfile(abs_path)

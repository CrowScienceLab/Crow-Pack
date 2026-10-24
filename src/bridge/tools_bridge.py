"""Native dialogs and background jobs for packaging tools."""

import hashlib
import json
import os
import secrets
import string
import threading

from PySide6.QtCore import QMimeData, QObject, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QLineEdit

from ..engine.archive_manager import ArchiveManager
from ..engine.packaging_tools import (
    FORMATS,
    DragExportManager,
    batch_extract,
    checksum_manifest,
    convert_archive,
    create_cbz,
    sha256,
    verify_checksum,
)


class ToolsBridge(QObject):
    toolFinished = Signal(str)
    dragStatus = Signal(str)
    _dragReady = Signal(str)

    def __init__(self):
        super().__init__()
        self._job = None
        self._drag_manager = None
        self._drag_cache = None
        self._drag_job = None
        self._dragReady.connect(self._finish_drag, Qt.QueuedConnection)

    @Slot(str, result=str)
    def generatePassword(self, mode):
        if mode == "phrase":
            # Six independently selected words from a 256-word compositional vocabulary.
            first = [
                "amber",
                "blue",
                "calm",
                "dawn",
                "eager",
                "frost",
                "green",
                "hazy",
                "ivory",
                "jade",
                "kind",
                "lunar",
                "merry",
                "nova",
                "opal",
                "pure",
            ]
            second = [
                "bird",
                "cloud",
                "dune",
                "elm",
                "fern",
                "glade",
                "hill",
                "isle",
                "lake",
                "moon",
                "nest",
                "oak",
                "pine",
                "rain",
                "star",
                "wave",
            ]
            return "-".join(secrets.choice(first) + secrets.choice(second) for _ in range(8))
        return "".join(secrets.choice(string.ascii_letters + string.digits + "!@#%+-_") for _ in range(24))

    @Slot(str)
    def copyText(self, value):
        QApplication.clipboard().setText(value)

    @Slot(str, result=str)
    def requestPassword(self, label):
        password, ok = QInputDialog.getText(self.parent_widget, "CrowPack", label, QLineEdit.Password)
        return password if ok else ""

    @Slot(str)
    def runTool(self, options_json):
        if self._job and self._job.is_alive():
            self.toolFinished.emit(json.dumps({"success": False, "error": "다른 작업이 실행 중입니다."}))
            return
        try:
            options = json.loads(options_json)
            action = options["action"]
            paths = options.get("paths", [])
            output = ""
            if action in {"convert", "cbz", "privacy", "split"}:
                if action == "cbz":
                    suffix = ".cbz"
                elif action == "privacy":
                    suffix = ".7z"
                else:
                    suffix = FORMATS.get(options.get("format"), ".zip")
                default = "result" + suffix
                output, _ = QFileDialog.getSaveFileName(self.parent_widget, "저장 위치", default, "All files (*)")
                if not output:
                    self.toolFinished.emit(json.dumps({"success": False, "cancelled": True}))
                    return
            elif action == "batch":
                output = QFileDialog.getExistingDirectory(self.parent_widget, "해제할 폴더")
                if not output:
                    self.toolFinished.emit(json.dumps({"success": False, "cancelled": True}))
                    return

            def work():
                try:
                    def progress(current, total, name):
                        if max(current, total) > 2_147_483_647:
                            self.progressEvent.emit(int(current * 100 / max(1, total)), 100, name)
                        else:
                            self.progressEvent.emit(current, total, name)
                    password = options.get("password") or None
                    if action == "convert":
                        result = convert_archive(
                            paths[0],
                            output,
                            options["format"],
                            password,
                            options.get("outputPassword") or None,
                            progress,
                        )
                    elif action == "cbz":
                        result = create_cbz(paths, output, options.get("renumber", True), progress)
                    elif action == "batch":
                        result = batch_extract(paths, output, options.get("mode", "new_folder"), password, progress)
                    elif action == "privacy":
                        if not options.get("outputPassword"):
                            raise ValueError("파일명까지 암호화하려면 비밀번호가 필요합니다.")
                        result = ArchiveManager.create_archive(
                            paths,
                            output,
                            "7Z",
                            password=options["outputPassword"],
                            progress_callback=progress,
                        )
                    elif action == "split":
                        split_size = int(options.get("splitSize") or 0)
                        if split_size <= 0:
                            raise ValueError("분할 크기를 선택하세요.")
                        result = ArchiveManager.create_archive(
                            paths,
                            output,
                            options.get("format", "ZIP"),
                            split_size_mb=split_size,
                            progress_callback=progress,
                        )
                    elif action == "manifest":
                        result = checksum_manifest(paths, output, progress)
                    elif action == "verify":
                        result = verify_checksum(paths[0], options["expected"])
                    elif action == "checksum":
                        result = [{"path": p, "sha256": sha256(p, progress)} for p in paths]
                    else:
                        raise ValueError("지원하지 않는 도구입니다.")
                    self.toolFinished.emit(
                        json.dumps({"success": True, "action": action, "result": result}, ensure_ascii=False)
                    )
                except Exception as exc:
                    self.toolFinished.emit(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False))
                finally:
                    options.clear()

            self._job = threading.Thread(target=work, daemon=False)
            self._job.start()
        except Exception as exc:
            self.toolFinished.emit(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False))

    @Slot(str, str, str, result=str)
    def dragArchiveItems(self, source, selected_json, password):
        try:
            if self._drag_job and self._drag_job.is_alive():
                return json.dumps({"success": False, "error": "드래그 파일을 준비 중입니다."})
            if self._drag_manager is None:
                self._drag_manager = DragExportManager()
            stat = os.stat(source)
            selected = json.loads(selected_json)
            cache_key = (source, stat.st_mtime_ns, stat.st_size, selected_json,
                         hashlib.sha256(password.encode()).digest())
            if self._drag_cache and self._drag_cache[0] == cache_key and all(os.path.exists(p) for p in self._drag_cache[1]):
                self._finish_drag(json.dumps({"paths": self._drag_cache[1]}))
                return json.dumps({"success": True})
            self.dragStatus.emit("드래그 복사할 파일을 준비 중입니다. 마우스 버튼을 누른 채 기다려 주세요.")

            def prepare():
                try:
                    paths = self._drag_manager.prepare(source, selected, password or None)
                    self._drag_cache = (cache_key, paths)
                    self._dragReady.emit(json.dumps({"paths": paths}))
                except Exception as exc:
                    self._dragReady.emit(json.dumps({"error": str(exc)}))

            self._drag_job = threading.Thread(target=prepare, daemon=False)
            self._drag_job.start()
            return json.dumps({"success": True, "preparing": True})
        except Exception as exc:
            return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)

    @Slot(str)
    def _finish_drag(self, payload):
        try:
            result = json.loads(payload)
            if "error" in result:
                self.dragStatus.emit("드래그 준비 실패: " + result["error"])
                return
            if not QApplication.mouseButtons() & Qt.LeftButton:
                self.dragStatus.emit("복사 준비 완료. 선택 항목을 다시 끌어 놓으세요.")
                return
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(path) for path in result["paths"]])
            drag = QDrag(getattr(self.parent_widget, 'web_view', self.parent_widget))
            drag.setMimeData(mime)
            action = drag.exec(Qt.CopyAction, Qt.CopyAction)
            self.dragStatus.emit("드래그 복사를 전달했습니다." if action == Qt.CopyAction else "드래그 복사가 취소되었습니다.")
        except Exception as exc:
            self.dragStatus.emit("드래그 복사 실패: " + str(exc))

    @Slot(result=str)
    def integrationStatus(self):
        from ..engine.shell_integration import association_status

        return json.dumps(association_status())

    @Slot(bool, result=str)
    def setShellIntegration(self, enabled):
        from ..engine.shell_integration import register, unregister_menu

        try:
            if enabled:
                register()
            else:
                unregister_menu()
            return json.dumps({"success": True})
        except Exception as exc:
            return json.dumps({"success": False, "error": str(exc)})

    @Slot()
    def openDefaultApps(self):
        if self._is_packaged():
            os.startfile("ms-settings:defaultapps?registeredAUMID=170231F2.CrowPack_9fbspzvkgt7f8%21CrowPack")
        else:
            from ..engine.shell_integration import register

            register(menu=False)
            os.startfile("ms-settings:defaultapps?registeredAppUser=CrowPack")

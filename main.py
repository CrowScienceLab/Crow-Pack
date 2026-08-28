"""
Crow Pack - Main Application Entry Point
Crow Pack v1.0K - 압축과 풀기 앱 (제작: Crow Science Lab)
"""

import json
import os
import sys

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow

from src.bridge.core_bridge import CoreBridge


class LocalOnlyPage(QWebEnginePage):
    """Keep the privileged WebChannel UI on bundled local resources only."""

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if is_main_frame and url.scheme().lower() not in {"file", "qrc", "about"}:
            return False
        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)

    def createWindow(self, window_type):
        return None


class DropAwareWebEngineView(QWebEngineView):
    """Receive native file URLs before Chromium discards their local paths."""

    pathsDropped = Signal(list)
    dragActiveChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    @staticmethod
    def _local_paths(event):
        return [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and self._local_paths(event):
            self.dragActiveChanged.emit(True)
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() and self._local_paths(event):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self.dragActiveChanged.emit(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        file_paths = self._local_paths(event)
        self.dragActiveChanged.emit(False)
        if file_paths:
            self.pathsDropped.emit(file_paths)
            event.acceptProposedAction()
            return
        super().dropEvent(event)


class CrowPackWindow(QMainWindow):
    def __init__(self, initial_files=None):
        super().__init__()
        # 창 상단 타이틀
        self.setWindowTitle("Crow Pack v1.0K - 압축과 풀기 앱")
        
        # 쾌적하고 균형 잡힌 창 크기 (780 x 520)
        self.resize(780, 520)
        self.setMinimumSize(680, 460)

        # 다크 윈도우 배경색 설정
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#0b0c10"))
        self.setPalette(palette)

        # WebEngine 뷰 초기화
        self.web_view = DropAwareWebEngineView(self)
        self.web_view.pathsDropped.connect(self._dispatch_dropped_paths)
        self.web_view.dragActiveChanged.connect(self._set_drag_active)
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)
        self.web_profile = QWebEngineProfile(self)
        self.web_profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        self.web_page = LocalOnlyPage(self.web_profile, self.web_view)
        self.web_view.setPage(self.web_page)
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, False)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        self.setCentralWidget(self.web_view)

        # WebChannel 설정
        self.channel = QWebChannel(self)
        self.bridge = CoreBridge(self)
        self.channel.registerObject("coreBridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # UI 파일 로드
        ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src", "ui", "index.html"))
        self.web_view.load(QUrl.fromLocalFile(ui_path))

        self.initial_files = initial_files or []
        self.web_view.loadFinished.connect(self._on_load_finished)

    def _on_load_finished(self, ok):
        if ok and self.initial_files:
            self._dispatch_dropped_paths(self.initial_files)

    def _dispatch_dropped_paths(self, file_paths):
        files_json = json.dumps(file_paths)
        js_code = f"if (window.handleNativeDrop) {{ window.handleNativeDrop({files_json}); }}"
        self.web_view.page().runJavaScript(js_code)

    def _set_drag_active(self, active):
        js_value = "true" if active else "false"
        self.web_view.page().runJavaScript(
            f"if (window.setNativeDragActive) {{ window.setNativeDragActive({js_value}); }}"
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Crow Pack")
    app.setOrganizationName("Crow Science Lab")

    initial_files = []
    if len(sys.argv) > 1:
        initial_files = [os.path.abspath(p) for p in sys.argv[1:] if os.path.exists(p)]

    window = CrowPackWindow(initial_files)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

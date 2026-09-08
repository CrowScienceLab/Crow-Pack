"""
Crow Pack - Main Application Entry Point
Crow Pack v1.5.0 - 압축과 풀기 앱 (제작: Crow Science Lab)
"""

import json
import os
import sys

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow

from src.bridge.core_bridge import CoreBridge


def bundled_path(*parts: str) -> str:
    """Return a source-tree or PyInstaller-bundled resource path."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


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
    def closeEvent(self, event):
        if self.bridge._job and self.bridge._job.is_alive():
            event.ignore()
            return
        if self.bridge._drag_manager:
            self.bridge._drag_manager.close()
        super().closeEvent(event)

    def __init__(self, initial_files=None):
        super().__init__()
        # 창 상단 타이틀
        self.setWindowTitle("Crow Pack v1.5.0 - 압축과 풀기 앱")
        self.setWindowIcon(QIcon(bundled_path("assets", "crow_pack.ico")))
        
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
        ui_path = bundled_path("src", "ui", "index.html")
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
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('CrowScienceLab.CrowPack')
    if '--register' in sys.argv or '--unregister' in sys.argv:
        from src.engine.shell_integration import register, unregister
        (unregister if '--unregister' in sys.argv else register)()
        return
    app = QApplication(sys.argv)
    app.setApplicationName("Crow Pack")
    app.setOrganizationName("Crow Science Lab")
    if '--default-apps' in sys.argv:
        os.startfile('ms-settings:defaultapps?registeredAppUser=Crow%20Pack')
        return
    app.setWindowIcon(QIcon(bundled_path("assets", "crow_pack.ico")))

    initial_files = []
    shell_action = None
    if '--shell' in sys.argv:
        index = sys.argv.index('--shell')
        shell_action = sys.argv[index + 1]
    if len(sys.argv) > 1:
        initial_files = [os.path.abspath(p) for p in sys.argv[1:] if os.path.exists(p)]

    window = CrowPackWindow(initial_files)
    if shell_action:
        # Explorer invokes Document verbs once per selected file; collect locally.
        import getpass
        server_name = 'CrowPack-shell-' + getpass.getuser()
        client = QLocalSocket()
        client.connectToServer(server_name)
        if client.waitForConnected(300):
            client.write((json.dumps([shell_action, initial_files]) + '\n').encode('utf-8'))
            client.waitForBytesWritten(1000)
            client.disconnectFromServer()
            return
        window.initial_files = []
        server = QLocalServer(window)
        server.setSocketOptions(QLocalServer.UserAccessOption)
        server.listen(server_name)
        pending = [shell_action, list(initial_files)]
        timer = QTimer(window)
        timer.setSingleShot(True)
        def dispatch():
            window.web_view.page().runJavaScript('window.handleShellAction(' + json.dumps(pending[0]) + ',' + json.dumps(pending[1]) + ');')
        timer.timeout.connect(dispatch)
        def receive():
            socket = server.nextPendingConnection()
            buffer = bytearray()
            def read():
                buffer.extend(bytes(socket.readAll()))
                if b'\n' not in buffer:
                    return
                action, paths = json.loads(buffer.decode('utf-8').split('\n')[0])
                if action == pending[0]:
                    pending[1].extend(p for p in paths if p not in pending[1])
                else:
                    pending[:] = [action, paths]
                timer.start(750)
                socket.disconnectFromServer()
            socket.readyRead.connect(read)
            read()
        server.newConnection.connect(receive)
        window.web_view.loadFinished.connect(lambda ok: timer.start(750) if ok else None)
    window.show()
    if '--smoke-test' in sys.argv:
        from pathlib import Path
        output = Path(sys.argv[sys.argv.index('--smoke-test') + 1]).resolve()
        def smoke():
            def checked(result):
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps({'version': CoreBridge.APP_VERSION, 'ui_ready': bool(result)}), encoding='utf-8')
                window.grab().save(str(output.with_suffix('.png')))
                app.exit(0 if result else 2)
            window.web_view.page().runJavaScript("Boolean(AppState.pyBridge && document.getElementById('packToolsButton') && document.getElementById('securityMode'))", checked)
        window.web_view.loadFinished.connect(lambda ok: QTimer.singleShot(1500, smoke) if ok else app.exit(2))
        QTimer.singleShot(15000, lambda: app.exit(3))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

"""Headless smoke checks for the bundled Qt WebEngine interface."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PySide6.QtCore import QMimeData, QPointF, Qt, QTimer, QUrl
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QApplication

from main import CrowPackWindow


def main() -> int:
    app = QApplication([])
    window = CrowPackWindow()

    expected = os.path.abspath(__file__)
    received = []
    window.web_view.pathsDropped.connect(received.extend)
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(expected)])
    drop_event = QDropEvent(
        QPointF(1, 1),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    window.web_view.dropEvent(drop_event)
    if not received or os.path.normcase(os.path.normpath(received[0])) != os.path.normcase(os.path.normpath(expected)):
        print("Native drop path smoke check failed.")
        return 1

    def on_dom_checked(result):
        print(f"UI DOM smoke: {bool(result)}")
        app.exit(0 if result else 2)

    def on_loaded(ok):
        if not ok:
            app.exit(3)
            return
        window.web_view.page().runJavaScript(
            "(() => {"
            "const buttons = Array.from(document.querySelectorAll('button[id]'));"
            "if (!buttons.length || buttons.some(button => typeof button.onclick !== 'function')) return false;"
            "if (typeof hideArchiveContextMenu !== 'function' || "
            "typeof window.setNativeDragActive !== 'function') return false;"
            "showExplorerView({format:'ZIP', filename:'smoke.zip', file_path:'smoke.zip', "
            "file_count:1, dir_count:0, uncompressed_size:10, compressed_size:8, "
            "compression_ratio:20, is_read_only:false, items:[{name:'sample.png', "
            "size:10, compressed_size:8, is_dir:false}]});"
            "const checkbox = document.querySelector('.item-chk');"
            "checkbox.click();"
            "if (!checkbox.checked || !AppState.selectedItems.has('sample.png')) return false;"
            "document.querySelector('#tblExplorerBody tr').dispatchEvent(new MouseEvent('contextmenu', "
            "{bubbles:true, cancelable:true, clientX:20, clientY:20}));"
            "if (!document.getElementById('archiveContextMenu').classList.contains('show')) return false;"
            "showHomeView(); window.setNativeDragActive(true);"
            "const neon = document.getElementById('homeDropZone').classList.contains('dragover');"
            "window.setNativeDragActive(false);"
            "return neon && typeof window.handleNativeDrop === 'function';"
            "})()",
            on_dom_checked,
        )

    window.web_view.loadFinished.connect(on_loaded)
    QTimer.singleShot(15_000, lambda: app.exit(4))
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

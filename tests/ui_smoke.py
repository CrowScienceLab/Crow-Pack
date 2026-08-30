"""Headless smoke checks for the bundled Qt WebEngine interface."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_OPENGL", "angle")
os.environ.setdefault("QT_ANGLE_PLATFORM", "warp")
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu --disable-gpu-compositing --no-sandbox --single-process",
)

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
            "if (document.querySelector('[data-tooltip][title]')) return false;"
            "if (typeof hideArchiveContextMenu !== 'function' || "
            "typeof window.setNativeDragActive !== 'function') return false;"
            "showExplorerView({format:'ZIP', filename:'smoke.zip', file_path:'smoke.zip', "
            "file_count:3, dir_count:0, uncompressed_size:30, compressed_size:24, "
            "compression_ratio:20, is_read_only:false, items:[{name:'sample.png', "
            "size:10, compressed_size:8, is_dir:false},{name:'second.txt',size:10,compressed_size:8,is_dir:false},"
            "{name:'third.txt',size:10,compressed_size:8,is_dir:false}]});"
            "let rows = Array.from(document.querySelectorAll('#tblExplorerBody tr'));"
            "if (AppState.selectedItems.size !== 3 || Array.from(document.querySelectorAll('.item-chk')).some(c => !c.checked)) return false;"
            "rows[0].dispatchEvent(new MouseEvent('click',{bubbles:true}));"
            "rows = Array.from(document.querySelectorAll('#tblExplorerBody tr'));"
            "rows[2].dispatchEvent(new MouseEvent('click',{bubbles:true,shiftKey:true}));"
            "if (AppState.selectedItems.size !== 0) return false;"
            "rows = Array.from(document.querySelectorAll('#tblExplorerBody tr'));"
            "rows[1].dispatchEvent(new MouseEvent('click',{bubbles:true,ctrlKey:true}));"
            "rows = Array.from(document.querySelectorAll('#tblExplorerBody tr'));"
            "rows[0].dispatchEvent(new MouseEvent('mousedown',{bubbles:true,button:2,buttons:2}));"
            "rows[2].dispatchEvent(new MouseEvent('mouseenter',{bubbles:true,button:2,buttons:2}));"
            "window.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,button:2}));"
            "rows[2].dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:20,clientY:20}));"
            "if (AppState.selectedItems.size !== 3) return false;"
            "document.querySelector('#tblExplorerBody tr').dispatchEvent(new MouseEvent('contextmenu', "
            "{bubbles:true, cancelable:true, clientX:20, clientY:20}));"
            "if (!document.getElementById('archiveContextMenu').classList.contains('show')) return false;"
            "showHomeView(); window.setNativeDragActive(true);"
            "const neon = document.getElementById('homeDropZone').classList.contains('dragover');"
            "window.setNativeDragActive(false);"
            "if (document.getElementById('btnToolCreateIso') || document.getElementById('btnToolOpenIso')) return false;"
            "document.getElementById('btnToolIsoImage').click();"
            "if (!document.getElementById('modalIsoImage').classList.contains('active')) return false;"
            "if (AppState.isoTab !== 'read' || document.getElementById('isoReadPanel').hidden) return false;"
            "window.setNativeDragActive(true);"
            "const isoNeon = document.getElementById('isoOpenDropZone').classList.contains('dragover');"
            "window.setNativeDragActive(false);"
            "document.getElementById('btnIsoTabCreate').click();"
            "if (AppState.isoTab !== 'create' || document.getElementById('isoCreatePanel').hidden) return false;"
            "document.getElementById('btnCancelIsoImage').click();"
            "document.getElementById('btnToolPdfOptimize').click();"
            "if (!document.getElementById('modalPdfOptimize').classList.contains('active')) return false;"
            "document.querySelector('input[name=\"pdfPreset\"][value=\"compact\"]').click();"
            "const presetOk = document.querySelector('input[name=\"pdfPreset\"]:checked').value === 'compact';"
            "if (!document.querySelector('input[name=\"pdfPreset\"][value=\"extreme\"]')) return false;"
            "document.getElementById('btnCancelPdfOptimize').click();"
            "applyTheme('bright-skyblue');"
            "if (document.body.dataset.theme !== 'bright-skyblue') return false;"
            "applyTheme('white-pink');"
            "if (document.body.dataset.theme !== 'white-pink') return false;"
            "applyTheme('dark'); applyLanguage('en');"
            "const englishOk = document.querySelector('[data-i18n=\"nav.info\"]').textContent === 'Help & Info';"
            "applyLanguage('ko');"
            "return neon && isoNeon && presetOk && englishOk && typeof window.handleNativeDrop === 'function';"
            "})()",
            on_dom_checked,
        )

    window.web_view.loadFinished.connect(on_loaded)
    QTimer.singleShot(15_000, lambda: app.exit(4))
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

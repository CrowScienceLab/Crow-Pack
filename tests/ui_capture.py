"""Capture actual Qt WebEngine layouts for packaging QA."""
import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from main import CrowPackWindow
from src.bridge.core_bridge import CoreBridge


def main():
    app = QApplication([])
    store_mode = os.environ.get('CROW_STORE_CAPTURE') == '1'
    if store_mode:
        CoreBridge._is_packaged = staticmethod(lambda: True)
    window = CrowPackWindow()
    window.resize(1366, 768)
    output = Path('work/store-screenshots' if store_mode else 'work/ui-qa')
    output.mkdir(parents=True, exist_ok=True)
    scripts = [
        ('home', "showHomeView();"),
        ('security', "openNewCompressModal(); document.getElementById('securityMode').value='private';document.getElementById('securityMode').dispatchEvent(new Event('change'));"),
        ('tools', "closeNewCompressModal();openPackTools([], 'convert');"),
        ('settings', "document.getElementById('packTools').classList.remove('active');document.getElementById('packSettings').classList.add('active');"),
        ('light', "document.getElementById('packSettings').classList.remove('active');applyTheme('white-pink');")
    ]
    def capture():
        if not scripts:
            app.quit()
            return
        name, script = scripts.pop(0)
        def save():
            window.grab().save(str(output / (name + '.png')))
            capture()
        window.web_view.page().runJavaScript(script, lambda _: QTimer.singleShot(600, save))
    window.web_view.loadFinished.connect(lambda ok: QTimer.singleShot(700, capture) if ok else app.exit(2))
    window.show()
    QTimer.singleShot(15000, app.quit)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())

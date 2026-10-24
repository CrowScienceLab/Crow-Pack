"""Actual WebEngine regression: parent icon and visible drag roots."""
import json
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from main import CrowPackWindow


def main():
    app = QApplication([])
    window = CrowPackWindow()

    def loaded(ok):
        if not ok:
            app.exit(2)
            return
        script = r'''(() => { try {
            const errors=[], payloads=[];
            const realBridge=AppState.pyBridge;
            showExplorerView({format:'ZIP',filename:'nested.zip',file_path:'nested.zip',
              items:[{name:'root/a/one/same.txt',size:1,is_dir:false},
                     {name:'root/b/two/same.txt',size:1,is_dir:false},
                     {name:'root/empty/',size:0,is_dir:true}],
              file_count:2,dir_count:1,uncompressed_size:2,compressed_size:2});
            AppState.currentDirectory='root/'; renderExplorer();
            const parent=document.querySelector('#tblExplorerBody tr');
            if(parent.textContent.includes('undefined') || !parent.querySelector('svg')) errors.push('parent icon');
            AppState.pyBridge={dragArchiveItems:(source, selected, password, callback)=>{
              payloads.push(JSON.parse(selected)); callback('{"success":true}');
            }};
            function drag(name) {
              const row=[...document.querySelectorAll('#tblExplorerBody tr')].find(r=>r.dataset.fullName===name);
              row.dispatchEvent(new PointerEvent('pointerdown',{button:0,buttons:1,clientX:10,clientY:10}));
              row.dispatchEvent(new PointerEvent('pointermove',{buttons:1,clientX:30,clientY:10}));
              row.dispatchEvent(new PointerEvent('pointerup',{button:0}));
            }
            drag('root/a/');
            if(JSON.stringify(payloads[0])!==JSON.stringify(['root/a/','root/b/'])) errors.push('multi folder roots');
            AppState.selectedItems.clear(); renderExplorer(); drag('root/empty/');
            if(JSON.stringify(payloads[1])!==JSON.stringify(['root/empty/'])) errors.push('empty root');
            AppState.currentDirectory='root/a/'; renderExplorer(); drag('root/a/one/');
            if(JSON.stringify(payloads[2])!==JSON.stringify(['root/a/one/'])) errors.push('nested visible root');
            AppState.pyBridge=realBridge;
            return JSON.stringify({errors});
        } catch(e) { return JSON.stringify({errors:[String(e),e.stack]}); } })()'''

        def checked(result):
            print('WebEngine drag and parent regression:', result)
            app.exit(0 if result and json.loads(result).get('errors') == [] else 1)
        window.web_view.page().runJavaScript(script, checked)

    window.web_view.loadFinished.connect(lambda ok: QTimer.singleShot(500, lambda: loaded(ok)))
    window.show()
    QTimer.singleShot(15000, lambda: app.exit(3))
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())

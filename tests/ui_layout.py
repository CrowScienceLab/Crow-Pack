"""Real WebEngine bounds checks for the default home, tools and settings layouts."""

import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from main import CrowPackWindow


def main():
    app = QApplication([])
    window = CrowPackWindow()
    cases = [
        (width, height, language, theme, view)
        for width, height in ((680, 460), (780, 520), (960, 620))
        for language in ("ko", "en")
        for theme in ("dark", "bright-skyblue", "white-pink")
        for view in ("home", "tools", "settings", "privacy", "split", "batch", "cbz")
    ]
    results = []
    output = Path("work/ui-qa") / ("scale-" + os.environ.get("QT_SCALE_FACTOR", "1"))
    output.mkdir(parents=True, exist_ok=True)

    def step():
        if not cases:
            (output / "layout.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
            failures = sum(bool(result["errors"]) for result in results)
            print(f"Layout cases: {len(results)}, failures: {failures}")
            app.exit(1 if failures else 0)
            return
        width, height, language, theme, view = cases.pop(0)
        window.resize(width, height)
        target_id = "packSettings" if view == "settings" else "packTools"
        script = f"""
            applyLanguage('{language}'); applyTheme('{theme}');
            document.querySelectorAll('.layer-modal-backdrop').forEach(x=>x.classList.remove('active'));
            showHomeView();
            if ('{view}' === 'tools') openPackTools([], 'convert');
            if (['privacy','split','batch','cbz'].includes('{view}')) openPackTools([], '{view}');
            if ('{view}' === 'settings') document.getElementById('packSettings').classList.add('active');
        """

        def measure():
            js = f"""(() => {{
                const errors=[];
                const inside=(node,label)=>{{
                    const r=node.getBoundingClientRect();
                    if(r.left < -1 || r.top < -1 || r.right > innerWidth+1 || r.bottom > innerHeight+1)
                        errors.push(label+' outside viewport');
                }};
                if(document.documentElement.scrollHeight > innerHeight+1 || document.body.scrollHeight > innerHeight+1)
                    errors.push('page vertical scrollbar');
                inside(document.querySelector('.crow-navbar'),'navbar');
                if('{view}' === 'home') {{
                    inside(document.getElementById('homeDropZone'),'home');
                    const home=document.getElementById('viewHome');
                    if(home.scrollHeight > home.clientHeight+1) errors.push('home overflow');
                }} else {{
                    const modal=document.querySelector('#{target_id} .compact-modal');
                    const body=modal.querySelector('.modal-body'); inside(modal,'modal');
                    if(body.scrollHeight > body.clientHeight+1 && getComputedStyle(body).overflowY === 'hidden')
                        errors.push('modal content clipped');
                }}
                if(['tools','privacy','split','batch','cbz'].includes('{view}')) {{
                    const tabs=[...document.querySelectorAll('.pack-tool-tab')];
                    if(tabs.length !== 5 || tabs.some(x=>!x.offsetWidth)) errors.push('five tools not visible');
                    for (const tab of tabs) {{
                        const label = tab.lastElementChild;
                        if(label.scrollHeight > label.clientHeight+1) errors.push('tool label clipped');
                    }}
                    if(document.querySelector('select#packAction')) errors.push('tool dropdown exists');
                }}
                if('{view}' === 'settings' && document.querySelector('#packSettings svg'))
                    errors.push('settings contains icon');
                if('{view}' === 'settings') {{
                    const body=document.querySelector('#packSettings .modal-body');
                    if(innerWidth >= 700 && innerHeight >= 480 && body.scrollHeight > body.clientHeight+1)
                        errors.push('unnecessary settings scrollbar');
                    for (const section of document.querySelectorAll('#packSettings .settings-section')) {{
                        if(section.scrollHeight > section.clientHeight+1) errors.push('settings section clipped');
                    }}
                    for (const choice of document.querySelectorAll('#packSettings .theme-choice')) {{
                        const box = choice.getBoundingClientRect();
                        const label = choice.lastElementChild.getBoundingClientRect();
                        if(label.bottom > box.bottom+1 || label.right > box.right+1 || label.top < box.top-1)
                            errors.push('theme label clipped');
                    }}
                }}
                return errors;
            }})()"""

            def checked(errors):
                results.append({"width": width, "height": height, "language": language,
                                "theme": theme, "view": view, "errors": errors or []})
                QTimer.singleShot(100, step)

            window.web_view.page().runJavaScript(js, checked)

        window.web_view.page().runJavaScript(script, lambda _: QTimer.singleShot(100, measure))

    window.web_view.loadFinished.connect(lambda ok: QTimer.singleShot(400, step) if ok else app.exit(2))
    window.show()
    QTimer.singleShot(90_000, lambda: app.exit(3))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

"""Qt WebEngine checks for circular swatches and truthful update status."""
import json
import sys
import tempfile
from pathlib import Path

from pypdf import PdfWriter
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from main import CrowPackWindow
from src.engine.pdf_optimizer import PdfOptimizer


def main():
    app = QApplication([])
    window = CrowPackWindow()
    with tempfile.TemporaryDirectory() as workspace:
        sample = Path(workspace) / 'sample.pdf'
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.add_blank_page(width=100, height=100)
        writer.write(sample)
        analysis = PdfOptimizer.analyze(str(sample))

    def run(ok):
        if not ok:
            app.exit(2)
            return
        script = r'''(() => { try {
            const errors=[];
            document.getElementById('packSettings').classList.add('active');
            for (const swatch of document.querySelectorAll('#packSettings .theme-swatch')) {
                const r=swatch.getBoundingClientRect(), css=getComputedStyle(swatch);
                if(Math.abs(r.width-r.height)>0.1 || r.width<17) errors.push('non-circular swatch');
                if(!css.backgroundImage.includes('50%')) errors.push('swatch split not half');
            }
            const status=document.getElementById('packUpdateStatus');
            for (const lang of ['ko','en']) {
                applyLanguage(lang);
                handleUpdateCheck({success:false,error_code:'rate_limit',error:'HTTP 403'},false);
                if(status.textContent.includes('최신 버전입니다') || status.textContent.includes('up to date')) errors.push('false current status');
                if(status.textContent.includes(' / ')) errors.push('mixed language status');
                if(status.title!=='HTTP 403') errors.push('missing error details');
                handleUpdateCheck({success:true,update_available:false,version:'1.7'},false);
                if(!status.textContent.includes(lang==='ko'?'최신':'up to date')) errors.push('missing current status');
                if(status.title) errors.push('stale error tooltip');
            }
            showProgress('Opening archive');
            if (document.getElementById('progressFileText').textContent !== 'Preparing…') errors.push('English progress preparation');
            finishProgress('Saved');
            if (document.getElementById('progressTitleText').textContent !== 'Done') errors.push('English progress completion');
            hideProgress();
            document.querySelector('input[name="radEncoding"][value="cp949"]').checked = true;
            document.getElementById('btnApplyCodePage').click();
            const encoding = document.getElementById('btnToolCodePage');
            if (encoding.getAttribute('aria-label') !== 'Encoding: Korean (CP949)') errors.push('English encoding label');
            renderPdfAnalysis(PDF_ANALYSIS);
            const pdf = document.getElementById('pdfAnalysisSummary');
            if (!pdf.textContent.includes('2 pages') || !pdf.textContent.includes('Recommended: Lossless Cleanup')) errors.push('English PDF analysis');
            document.querySelector('input[name="pdfPreset"][value="high"]').checked = true;
            if (!document.querySelector('[data-i18n="info.author"]').textContent.includes('© 2026 Crow Science Lab')) errors.push('Missing attribution');
            applyLanguage('ko');
            if (!encoding.getAttribute('aria-label').includes('한국어') || !pdf.textContent.includes('2쪽')) errors.push('Existing reports do not follow language changes');
            if (document.querySelector('input[name="pdfPreset"]:checked').value !== 'high') errors.push('Language changed selected PDF preset');
            const bridge = AppState.pyBridge;
            let githubChecks = 0, storeOpens = 0;
            AppState.pyBridge = {
                integrationStatus: callback => callback(JSON.stringify([
                    {extension:'.zip',handler:'Other archiver',assigned:true,is_crowpack:false},
                    {extension:'.7z',handler:'',assigned:false,is_crowpack:false},
                    {extension:'.cbz',handler:'CrowPack',assigned:true,is_crowpack:true}
                ])),
                createDesktopShortcut: callback => callback(JSON.stringify({success:true,state:'created'})),
                checkForUpdatesAsync: () => githubChecks++,
                openStoreUpdate: callback => { storeOpens++; callback(JSON.stringify({success:true})); }
            };
            const previousChannel = isPackagedDistribution;
            isPackagedDistribution = true;
            applyLanguage('en');
            document.getElementById('packDefaults').click();
            const setup = document.getElementById('packWindowsSetup');
            const list = document.getElementById('packAssociationList');
            if (!setup.open || list.children.length !== 3 || !list.textContent.includes('No default app') || !list.textContent.includes('Other archiver')) errors.push('Windows association details');
            const shortcut = document.getElementById('packCreateShortcut');
            shortcut.click();
            if (!document.getElementById('packWindowsSetupStatus').textContent.includes('Desktop shortcut created')) errors.push('Shortcut feedback');
            document.getElementById('packFinishWindowsSetup').click();
            if (setup.open) errors.push('Windows setup did not close');
            requestUpdateCheck(false);
            requestUpdateCheck(true);
            if (githubChecks !== 0 || storeOpens !== 1) errors.push('Wrong update channel');
            AppState.pyBridge = bridge;
            isPackagedDistribution = previousChannel;
            applyLanguage('ko');
            document.getElementById('packSettings').classList.remove('active');
            openInfoModal();
            const help = document.querySelector('#modalInfoApp .modal-body');
            const helpViewport = {width:innerWidth, height:innerHeight, dpr:devicePixelRatio,
                scroll:help.scrollHeight, client:help.clientHeight};
            closeInfoModal();
            return JSON.stringify({errors, helpViewport});
        } catch(e) { return JSON.stringify({errors:[String(e)]}); } })()'''.replace('PDF_ANALYSIS', json.dumps(analysis))

        def checked(raw):
            print('Settings regression:', raw)
            app.exit(0 if raw and json.loads(raw)['errors'] == [] else 1)
        window.web_page.runJavaScript(script, checked)

    window.web_view.loadFinished.connect(lambda ok: QTimer.singleShot(700, lambda: run(ok)))
    window.show()
    QTimer.singleShot(15000, lambda: app.exit(3))
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())

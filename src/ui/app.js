/**
 * CrowPack v1.7 - Frontend Interaction Logic
 * 칠흑 까마귀 테마, 툴바 컨텍스트 전환, 플로팅 툴팁 엔진 및 드래그앤드롭
 */

// 바이트 포맷터
function formatBytes(bytes, decimals = 1) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// 전역 상태
const AppState = {
  currentView: 'home', // 'home' | 'explorer'
  currentArchiveInfo: null,
  currentDirectory: '', // 탐색기 내부 가상 디렉터리
  explorerFilter: '',
  selectedItems: new Set(),
  selectionAnchorIndex: null,
  rightDragSelecting: false,
  rightDragMoved: false,
  rightDragStartName: '',
  compressSourcePaths: [],
  isoSourcePaths: [],
  isoTab: 'read',
  pdfInputPath: '',
  pdfAnalysis: null,
  selectedEncoding: 'auto',
  language: 'ko',
  theme: 'dark',
  lastExtractedFolder: null,
  contextEntry: null,
  pyBridge: null
};

const IMAGE_PREVIEW_PATTERN = /\.(bmp|gif|jpe?g|png|webp)$/i;
const PDF_FILE_PATTERN = /\.pdf$/i;
const ARCHIVE_FILE_PATTERN = /\.(zip|7z|rar|tar|gz|tgz|bz2|tbz2|xz|txz|alz|egg|cab|iso|cbz)$/i;
const EXEC_FILE_PATTERN = /\.(exe|msi|bat|cmd|ps1|vbs|js|scr|com)$/i;
const ISO_PATTERN = /\.iso$/i;

const FORMAT_TOOLTIPS = {
  ko: {
    ZIP: 'ZIP · 읽기/해제/생성 (AES-256 지원)',
    '7Z': '7Z · 고압축 및 파일명 암호화 지원',
    RAR: 'RAR · 목록 조회 및 해제 지원',
    'TAR.GZ': 'TAR.GZ · 리눅스/서버 표준 압축·해제',
    'TAR.XZ': 'TAR.XZ · 리눅스 고압축·해제',
    ALZ: 'ALZ · 읽기 및 실험적 해제 지원',
    EGG: 'EGG · 읽기 및 실험적 해제 지원',
    CAB: 'CAB · Windows 캐비닛 읽기/해제',
    ISO: 'ISO · 데이터 ISO 탐색·복사·생성 지원'
  },
  en: {
    ZIP: 'ZIP · Browse, extract & create (AES-256)',
    '7Z': '7Z · Ultra compression & filename encryption',
    RAR: 'RAR · Browse & extract support',
    'TAR.GZ': 'TAR.GZ · Linux/Server standard archive',
    'TAR.XZ': 'TAR.XZ · High-ratio Linux archive',
    ALZ: 'ALZ · Browse & experimental extract',
    EGG: 'EGG · Browse & experimental extract',
    CAB: 'CAB · Windows cabinet browse & extract',
    ISO: 'ISO · Browse, copy & create data ISO'
  }
};

const uiText = (ko, en) => AppState.language === 'en' ? en : ko;

function showToast(message) {
  const toast = document.getElementById('crowToast');
  if (!toast || !message) return;
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.remove('show'), 2200);
}
window.showCrowToast = showToast;

function openOfficialLink(linkKey) {
  if (!AppState.pyBridge || !AppState.pyBridge.openExternalLink) return;
  AppState.pyBridge.openExternalLink(linkKey, (resJson) => {
    const res = JSON.parse(resJson);
    if (!res.success && res.error) alert(uiText('링크를 열 수 없습니다', 'Could not open the link') + '\n' + res.error);
  });
}

const TRANSLATIONS = {
  ko: {
    'nav.iso': 'ISO 이미지',
    'nav.pdf': 'PDF 용량 조절',
    'nav.update': '업데이트 확인',
    'nav.association': '앱 확장자 연결',
    'nav.info': '도움말',
    'exp.extractHere': '여기에 풀기',
    'exp.extractCustom': '폴더 지정',
    'exp.add': '추가',
    'exp.delete': '삭제',
    'exp.test': '검사',
    'exp.encoding': '인코딩',
    'dock.title': '빠른 도구',
    'dock.pdf': 'PDF 용량',
    'dock.iso': 'ISO 이미지',
    'dock.convert': '포맷 변환',
    'dock.batch': '일괄 해제',
    'dock.cbz': 'CBZ 만들기',
    'dock.privacy': '파일명 암호화',
    'link.releases': '릴리스',
    'link.privacy': '개인정보·보안',
    'home.localBadge': '100% 로컬 처리',
    'iso.title': 'ISO 이미지',
    'iso.readTab': 'ISO 읽기',
    'iso.createTab': 'ISO 만들기',
    'iso.readHelp': 'ISO 안의 파일을 안전하게 탐색하고 원하는 항목을 폴더로 복사합니다.',
    'iso.dropTitle': 'ISO 이미지를 이곳에 끌어다 놓으세요',
    'iso.dropHint': '또는 아래 버튼으로 ISO 파일을 선택하세요.',
    'iso.select': 'ISO 파일 선택',
    'iso.createHelp': '일반 데이터 ISO를 만듭니다. Windows용 Joliet와 Linux용 Rock Ridge 파일명을 함께 기록합니다.',
    'iso.empty': 'ISO에 넣을 파일이나 폴더를 추가하세요.',
    'iso.addFiles': '+ 파일 추가',
    'iso.addFolder': '+ 폴더 추가',
    'iso.volume': '디스크 이름',
    'iso.limit': '부팅 ISO와 4 GiB 이상 단일 파일은 지원하지 않습니다. 원본 파일은 변경되지 않습니다.',
    'iso.create': 'ISO 만들기',
    'common.clear': '비우기',
    'common.close': '닫기',
    'common.confirm': '확인',
    'info.title': '도움말',
    'info.author': '© 2026 Crow Science Lab',
    'info.summary': '압축 파일과 ISO 이미지를 안전하게 탐색·복사',
    'info.version': '버전 v1.7',
    'info.linksTitle': '공식 링크 및 배포 채널',
    'info.linkGithubSub': '공식 원본 및 이슈 제보',
    'info.linkReleasesTitle': '릴리스 노트',
    'info.linkReleasesSub': '버전 내역 및 설치 파일',
    'info.linkStoreSub': '스토어 제품 페이지',
    'info.linkPrivacyTitle': '개인정보·보안',
    'info.linkPrivacySub': '로컬 처리 정책 안내',
    'info.shortcuts': '단축키: Esc 창 닫기 · Ctrl+A 전체 선택 · Ctrl+F 목록 검색 · Backspace 상위 폴더',
    'info.help': '<strong>사용법 안내:</strong><br>• <strong>압축 해제</strong>: 압축 파일을 열면 상단 도구로 현재 폴더 또는 지정 폴더에 풀 수 있습니다.<br>• <strong>새로 압축</strong>: 파일/폴더를 끌어다 놓고 압축 프리셋·분할·암호를 설정합니다.<br>• <strong>ISO 이미지</strong>: 읽기 탭은 ISO를 탐색·복사하고, 만들기 탭은 일반 데이터 ISO를 생성합니다.<br>• <strong>PDF 용량 조절</strong>: 문서 구성을 분석한 뒤 다섯 가지 단계 중 하나를 선택하면 세부 설정은 자동 적용됩니다.',
    'settings.title': '화면 설정',
    'settings.language': '언어',
    'settings.theme': '색 테마',
    'theme.dark': 'Black (기본)'
  },
  en: {
    'nav.iso': 'ISO Image',
    'nav.pdf': 'PDF Size',
    'nav.update': 'Check Updates',
    'nav.association': 'File Associations',
    'nav.info': 'Help',
    'exp.extractHere': 'Extract Here',
    'exp.extractCustom': 'Extract To',
    'exp.add': 'Add',
    'exp.delete': 'Delete',
    'exp.test': 'Test',
    'exp.encoding': 'Encoding',
    'dock.title': 'Quick Tools',
    'dock.pdf': 'PDF Size',
    'dock.iso': 'ISO Image',
    'dock.convert': 'Convert',
    'dock.batch': 'Batch Extract',
    'dock.cbz': 'Create CBZ',
    'dock.privacy': 'Encrypt Names',
    'link.releases': 'Releases',
    'link.privacy': 'Privacy & Security',
    'home.localBadge': '100% Local Processing',
    'iso.title': 'ISO Image',
    'iso.readTab': 'Read ISO',
    'iso.createTab': 'Create ISO',
    'iso.readHelp': 'Browse an ISO safely and copy selected files to a folder.',
    'iso.dropTitle': 'Drop an ISO image here',
    'iso.dropHint': 'Or select an ISO file with the button below.',
    'iso.select': 'Select ISO File',
    'iso.createHelp': 'Create a data ISO with Windows Joliet and Linux Rock Ridge file names.',
    'iso.empty': 'Add files or folders to include in the ISO.',
    'iso.addFiles': '+ Add Files',
    'iso.addFolder': '+ Add Folder',
    'iso.volume': 'Volume label',
    'iso.limit': 'Bootable ISOs and individual files of 4 GiB or larger are not supported. Source files are unchanged.',
    'iso.create': 'Create ISO',
    'common.clear': 'Clear',
    'common.close': 'Close',
    'common.confirm': 'OK',
    'info.title': 'Help & About',
    'info.author': '© 2026 Crow Science Lab',
    'info.summary': 'Safely browse, extract, and copy archives and ISO images',
    'info.version': 'Version v1.7',
    'info.linksTitle': 'Official Links & Channels',
    'info.linkGithubSub': 'Official source and issue tracker',
    'info.linkReleasesTitle': 'Release Notes',
    'info.linkReleasesSub': 'Changelog & signed installers',
    'info.linkStoreSub': 'Store product listing',
    'info.linkPrivacyTitle': 'Privacy & Security',
    'info.linkPrivacySub': 'Offline processing policy',
    'info.shortcuts': 'Shortcuts: Esc Close modal · Ctrl+A Select all · Ctrl+F Filter · Backspace Parent folder',
    'info.help': '<strong>Quick guide:</strong><br>• <strong>Extract</strong>: Open an archive, then extract to the current folder or a chosen folder.<br>• <strong>Create archive</strong>: Drop files or folders, then choose a preset, splitting, and password.<br>• <strong>ISO Image</strong>: Read and copy from an ISO, or create a standard data ISO in the second tab.<br>• <strong>PDF Size</strong>: Analyze the document, then choose one of five presets and CrowPack applies the detailed settings.',
    'settings.title': 'Display settings',
    'settings.language': 'Language',
    'settings.theme': 'Color theme',
    'theme.dark': 'Black (default)'
  }
};

const STATIC_UI_TRANSLATIONS = {
  ko: {
    text: {
      '.brand-subtext': '압축과 풀기 앱',
      '#btnCardOpenArchive .action-card-title': '압축 파일 열기',
      '#btnCardNewCompress .action-card-title': '새로 압축하기',
      '.home-drop-hint': '또는 이곳에 압축 파일이나 압축할 파일/폴더들을 끌어다 놓으세요',
      '#tblExplorer thead th:nth-child(2)': '이름',
      '#tblExplorer thead th:nth-child(3)': '원본 크기',
      '#tblExplorer thead th:nth-child(4)': '압축 크기',
      '#tblExplorer thead th:nth-child(5)': '수정 일시',
      '#modalTitleNewCompress': '새로 압축하기',
      '#btnAddSourceFiles': '+ 파일 추가', '#btnAddSourceFolder': '+ 폴더 추가', '#btnClearSourceList': '비우기',
      '#btnCancelCompress': '취소', '#btnCompressHere': '이 폴더에 압축', '#btnCompressCustom': '폴더변경 압축',
      '#modalNewCompress .form-item:nth-child(1) .form-label': '시스템 최적화 프리셋',
      '#modalNewCompress .form-item:nth-child(2) .form-label': '압축 형식',
      '#modalNewCompress .form-item:nth-child(3) .form-label': '분할 압축',
      '#modalNewCompress .form-item:nth-child(4) .form-label': '압축률',
      '#selPresetMode option[value="windows"]': 'Windows 호환 (ZIP 표준)',
      '#selPresetMode option[value="linux"]': 'Linux / Server 배포 (TAR.GZ)',
      '#selPresetMode option[value="macos"]': 'macOS / 크로스 (UTF-8 ZIP)',
      '#selPresetMode option[value="ultra7z"]': '고압축 (7Z LZMA2)',
      '#selCompressFmt option[value="ZIP"]': 'ZIP (표준 호환)',
      '#selCompressFmt option[value="7Z"]': '7Z (초고압축)',
      '#selCompressFmt option[value="TAR.GZ"]': 'TAR.GZ (리눅스 배포)',
      '#selCompressFmt option[value="TAR.XZ"]': 'TAR.XZ (리눅스 고압축)',
      '#selSplitSize option[value="0"]': '분할 안 함',
      '#selSplitSize option[value="10"]': '10 MB (네이버/다음 메일)',
      '#selSplitSize option[value="25"]': '25 MB (Gmail 대용량)',
      '#selCompressLevel option[value="6"]': '보통 (권장)',
      '#selCompressLevel option[value="1"]': '빠름',
      '#selCompressLevel option[value="9"]': '최대 압축',
      '#selCompressLevel option[value="0"]': '압축 안 함',
      '#modalPdfOptimize .modal-title': 'PDF 용량 조절',
      '#modalPdfOptimize .modal-help-text': '먼저 문서를 분석하면 용량 구성과 권장 단계를 확인할 수 있습니다. 모든 처리는 이 컴퓨터 안에서만 진행됩니다.',
      '#btnAnalyzePdf': 'PDF 선택·분석',
      '.pdf-preset-card:nth-child(1) .pdf-preset-title': '무손실 정리',
      '.pdf-preset-card:nth-child(1) .pdf-preset-desc': '그림 변경 없이 내부 구조만 정리',
      '.pdf-preset-card:nth-child(2) .pdf-preset-title': '문서 최적화',
      '.pdf-preset-card:nth-child(2) .pdf-preset-desc': '인쇄용, 큰 그림 최대 약 2,480px',
      '.pdf-preset-card:nth-child(3) .pdf-preset-title': '균형',
      '.pdf-preset-card:nth-child(3) .pdf-preset-desc': '일반 공유용, 품질과 크기의 균형',
      '.pdf-preset-card:nth-child(3) .preset-badge': '권장',
      '.pdf-preset-card:nth-child(4) .pdf-preset-title': '최소 용량',
      '.pdf-preset-card:nth-child(4) .pdf-preset-desc': '화면 열람용, 가장 강한 그림 최적화',
      '.pdf-preset-card:nth-child(5) .pdf-preset-title': '극한 압축',
      '.pdf-preset-card:nth-child(5) .pdf-preset-desc': '페이지를 120 DPI 이미지로 재구성·문서 기능 손실 가능',
      '#modalPdfOptimize .preset-note': '외부 서버 전송 없음 · 원본 덮어쓰기 없음 · 전자서명·암호화 PDF 처리 안 함',
      '#btnCancelPdfOptimize': '취소', '#btnRunPdfOptimize': '선택한 품질로 저장',
      '#modalCodePage .modal-title': '코드페이지 / 한글 인코딩 설정',
      '#modalCodePage .modal-help-text': '압축 파일 내 한글 파일명 깨짐을 방지하기 위한 코드페이지를 선택하세요.',
      '#modalCodePage .form-row:nth-child(1) span': '자동 감지 & 한글 자동복원 (기본 권장)',
      '#modalCodePage .form-row:nth-child(2) span': '한국어 (CP949 / EUC-KR)',
      '#modalCodePage .form-row:nth-child(3) span': '유니코드 (UTF-8)',
      '#modalCodePage .form-row:nth-child(4) span': '일본어 (Shift-JIS / CP932)',
      '#modalCodePage .form-row:nth-child(5) span': '중국어 간체 (GBK / CP936)',
      '#modalCodePage .form-row:nth-child(6) span': '한글 자동복원 끄기 (Raw 원본)',
      '#btnApplyCodePage': '적용',
      '#ctxPreviewImage': '그림 미리보기', '#ctxOpenFile': '파일 열기',
      '#ctxCopyOut': '선택 항목을 폴더로 복사', '#ctxMoveOut': '선택 항목을 폴더로 이동',
      '#ctxDelete': '압축 파일에서 삭제', '#imagePreviewTitle': '그림 미리보기',
      '#btnProgressOpenFolder': '폴더 열기', '#btnProgressClose': '닫기'
    },
    html: {
      '#btnCardOpenArchive .action-card-desc': 'ZIP, 7Z, RAR, TAR 등<br>주요 포맷과 ISO 탐색',
      '#btnCardNewCompress .action-card-desc': '시스템별 최적화 압축<br>분할 압축 및 암호화 지원'
    }
  },
  en: {
    text: {
      '.brand-subtext': 'Archive Manager',
      '#btnCardOpenArchive .action-card-title': 'Open Archive',
      '#btnCardNewCompress .action-card-title': 'Create Archive',
      '.home-drop-hint': 'Or drop an archive, files, or folders here',
      '#tblExplorer thead th:nth-child(2)': 'Name',
      '#tblExplorer thead th:nth-child(3)': 'Original size',
      '#tblExplorer thead th:nth-child(4)': 'Packed size',
      '#tblExplorer thead th:nth-child(5)': 'Modified',
      '#modalTitleNewCompress': 'Create Archive',
      '#btnAddSourceFiles': '+ Add Files', '#btnAddSourceFolder': '+ Add Folder', '#btnClearSourceList': 'Clear',
      '#btnCancelCompress': 'Cancel', '#btnCompressHere': 'Save Here', '#btnCompressCustom': 'Choose Destination',
      '#modalNewCompress .form-item:nth-child(1) .form-label': 'Optimized preset',
      '#modalNewCompress .form-item:nth-child(2) .form-label': 'Archive format',
      '#modalNewCompress .form-item:nth-child(3) .form-label': 'Split archive',
      '#modalNewCompress .form-item:nth-child(4) .form-label': 'Compression level',
      '#selPresetMode option[value="windows"]': 'Windows compatible (ZIP)',
      '#selPresetMode option[value="linux"]': 'Linux / Server (TAR.GZ)',
      '#selPresetMode option[value="macos"]': 'macOS / Cross-platform (ZIP)',
      '#selPresetMode option[value="ultra7z"]': 'High compression (7Z LZMA2)',
      '#selCompressFmt option[value="ZIP"]': 'ZIP (Standard)',
      '#selCompressFmt option[value="7Z"]': '7Z (Ultra)',
      '#selCompressFmt option[value="TAR.GZ"]': 'TAR.GZ (Linux)',
      '#selCompressFmt option[value="TAR.XZ"]': 'TAR.XZ (Linux Ultra)',
      '#selSplitSize option[value="0"]': 'Do not split',
      '#selSplitSize option[value="10"]': '10 MB (Email)',
      '#selSplitSize option[value="25"]': '25 MB (Large mail)',
      '#selCompressLevel option[value="6"]': 'Normal (recommended)',
      '#selCompressLevel option[value="1"]': 'Fast',
      '#selCompressLevel option[value="9"]': 'Maximum',
      '#selCompressLevel option[value="0"]': 'Store only',
      '#modalPdfOptimize .modal-title': 'Adjust PDF Size',
      '#modalPdfOptimize .modal-help-text': 'Analyze the document first to see its size profile and recommended preset. Processing stays on this PC.',
      '#btnAnalyzePdf': 'Select & Analyze PDF',
      '.pdf-preset-card:nth-child(1) .pdf-preset-title': 'Lossless Cleanup',
      '.pdf-preset-card:nth-child(1) .pdf-preset-desc': 'Clean internal structure without changing images',
      '.pdf-preset-card:nth-child(2) .pdf-preset-title': 'Document Optimized',
      '.pdf-preset-card:nth-child(2) .pdf-preset-desc': 'For print, large images up to about 2,480 px',
      '.pdf-preset-card:nth-child(3) .pdf-preset-title': 'Balanced',
      '.pdf-preset-card:nth-child(3) .pdf-preset-desc': 'Recommended balance for everyday sharing',
      '.pdf-preset-card:nth-child(3) .preset-badge': 'Recommended',
      '.pdf-preset-card:nth-child(4) .pdf-preset-title': 'Smallest',
      '.pdf-preset-card:nth-child(4) .pdf-preset-desc': 'Strongest image optimization for screen viewing',
      '.pdf-preset-card:nth-child(5) .pdf-preset-title': 'Extreme',
      '.pdf-preset-card:nth-child(5) .pdf-preset-desc': 'Rebuild pages as 120 DPI images; document features may be lost',
      '#modalPdfOptimize .preset-note': 'No upload · No source overwrite · Signed/encrypted PDFs are not processed',
      '#btnCancelPdfOptimize': 'Cancel', '#btnRunPdfOptimize': 'Save with Selected Quality',
      '#modalCodePage .modal-title': 'Filename Encoding',
      '#modalCodePage .modal-help-text': 'Choose how CrowPack should recover legacy archive filenames.',
      '#modalCodePage .form-row:nth-child(1) span': 'Auto-detect and repair Korean names (recommended)',
      '#modalCodePage .form-row:nth-child(2) span': 'Korean (CP949 / EUC-KR)',
      '#modalCodePage .form-row:nth-child(3) span': 'Unicode (UTF-8)',
      '#modalCodePage .form-row:nth-child(4) span': 'Japanese (Shift-JIS / CP932)',
      '#modalCodePage .form-row:nth-child(5) span': 'Simplified Chinese (GBK / CP936)',
      '#modalCodePage .form-row:nth-child(6) span': 'Disable filename repair (raw names)',
      '#btnApplyCodePage': 'Apply',
      '#ctxPreviewImage': 'Preview Image', '#ctxOpenFile': 'Open File',
      '#ctxCopyOut': 'Copy Selected Items to Folder', '#ctxMoveOut': 'Move Selected Items to Folder',
      '#ctxDelete': 'Delete from Archive', '#imagePreviewTitle': 'Image Preview',
      '#btnProgressOpenFolder': 'Open Folder', '#btnProgressClose': 'Close'
    },
    html: {
      '#btnCardOpenArchive .action-card-desc': 'ZIP, 7Z, RAR, TAR and more<br>Browse archives and ISO images',
      '#btnCardNewCompress .action-card-desc': 'Optimized presets<br>Splitting and encryption'
    }
  }
};

function applyStaticUiTranslations(language) {
  const translations = STATIC_UI_TRANSLATIONS[language] || STATIC_UI_TRANSLATIONS.ko;
  Object.entries(translations.text).forEach(([selector, value]) => {
    const element = document.querySelector(selector);
    if (element) element.textContent = value;
  });
  Object.entries(translations.html).forEach(([selector, value]) => {
    const element = document.querySelector(selector);
    if (element) element.innerHTML = value;
  });
}

function savePreference(key, value) {
  try { localStorage.setItem(`crowPack.${key}`, value); } catch (_error) { /* private/local mode */ }
}

function loadPreference(key, fallback) {
  try { return localStorage.getItem(`crowPack.${key}`) || fallback; } catch (_error) { return fallback; }
}

function applyTheme(theme) {
  const allowed = new Set(['dark', 'bright-skyblue', 'white-pink']);
  AppState.theme = allowed.has(theme) ? theme : 'dark';
  document.body.dataset.theme = AppState.theme;
  const radio = document.querySelector(`input[name="appTheme"][value="${AppState.theme}"]`);
  if (radio) radio.checked = true;
  savePreference('theme', AppState.theme);
}

function applyLanguage(language) {
  AppState.language = TRANSLATIONS[language] ? language : 'ko';
  AppState.pyBridge?.setUiLanguage?.(AppState.language);
  const dictionary = TRANSLATIONS[AppState.language];
  const isEn = AppState.language === 'en';
  document.documentElement.lang = AppState.language;
  document.querySelectorAll('[data-i18n]').forEach((element) => {
    const translated = dictionary[element.dataset.i18n];
    if (translated !== undefined) element.textContent = translated;
  });
  document.querySelectorAll('[data-i18n-html]').forEach((element) => {
    const translated = dictionary[element.dataset.i18nHtml];
    if (translated !== undefined) element.innerHTML = translated;
  });
  applyStaticUiTranslations(AppState.language);
  if (window.applyPackLanguage) window.applyPackLanguage();
  const selector = document.getElementById('selAppLanguage');
  if (selector) selector.value = AppState.language;

  const filterInput = document.getElementById('explorerFilterInput');
  if (filterInput) {
    filterInput.placeholder = isEn ? 'Filter items (Ctrl+F)' : '목록 내 검색 (Ctrl+F)';
    filterInput.setAttribute('aria-label', isEn ? 'Filter archive items' : '목록 내 검색');
  }
  const pwdInput = document.getElementById('txtCompressPwd');
  if (pwdInput) {
    pwdInput.placeholder = isEn ? 'Enter password' : '비밀번호를 입력하세요.';
  }
  if (AppState.pdfAnalysis) renderPdfAnalysis(AppState.pdfAnalysis, false);
  else document.getElementById('pdfAnalysisSummary').textContent = uiText('분석할 PDF를 선택하세요.', 'Select a PDF to analyze.');
  refreshEncodingTooltip();

  const tooltipText = isEn
    ? ['Read or create an ISO image', 'Optimize PDF size with quality presets', 'Check for CrowPack updates', 'Connect CrowPack to Windows file extensions', 'Help, official links, language, and display theme']
    : ['ISO 이미지 읽기 또는 만들기', '품질 프리셋으로 PDF 용량 조절', 'CrowPack 업데이트 확인', 'Windows 기본 앱에 CrowPack 연결', '정보, 공식 링크, 언어 및 화면 테마 설정'];
  ['btnToolIsoImage', 'btnToolPdfOptimize', 'btnToolUpdate', 'btnToolAssociations', 'btnToolInfo'].forEach((id, index) => {
    const button = document.getElementById(id);
    if (!button) return;
    button.dataset.tooltip = tooltipText[index];
    button.setAttribute('aria-label', tooltipText[index]);
    button.removeAttribute('title');
  });

  const fmtMap = FORMAT_TOOLTIPS[AppState.language] || FORMAT_TOOLTIPS.ko;
  document.querySelectorAll('#formatBadgesRow .fmt-badge').forEach((badge) => {
    const tip = fmtMap[badge.dataset.fmt];
    if (tip) {
      badge.dataset.tooltip = tip;
      badge.setAttribute('aria-label', tip);
      badge.removeAttribute('title');
    }
  });

  const dockTips = isEn
    ? {
        btnQuickPdf: 'Analyze and optimize PDF size (5 presets)',
        btnQuickIso: 'Browse or create a data ISO image',
        btnQuickConvert: 'Convert archives between ZIP, 7Z, and TAR',
        btnQuickBatch: 'Extract multiple archives at once',
        btnQuickCbz: 'Create a naturally sorted CBZ comic archive',
        btnQuickPrivacy: 'Encrypt both file names and contents (7Z)'
      }
    : {
        btnQuickPdf: '분석 기반 5단계 PDF 용량 조절',
        btnQuickIso: 'ISO 이미지 탐색 및 생성',
        btnQuickConvert: '아카이브 포맷 안전 변환',
        btnQuickBatch: '여러 압축 파일 한 번에 풀기',
        btnQuickCbz: '자연 정렬 이미지 CBZ 생성',
        btnQuickPrivacy: '파일명·내용 모두 암호화 (7Z)'
      };
  Object.entries(dockTips).forEach(([id, tip]) => {
    const btn = document.getElementById(id);
    if (btn) {
      btn.dataset.tooltip = tip;
      btn.setAttribute('aria-label', tip);
      btn.removeAttribute('title');
    }
  });

  if (document.getElementById('compressFileListPreview')) renderCompressSourceList();
  if (document.getElementById('isoFileListPreview')) renderIsoSourceList();
  if (AppState.currentArchiveInfo) {
    showExplorerViewTooltips();
    updateExplorerStatusBar();
  }
  savePreference('language', AppState.language);
}

function setNativeDragActive(active) {
  const isoModal = document.getElementById('modalIsoImage');
  const useIsoReadZone = isoModal && isoModal.classList.contains('active') && AppState.isoTab === 'read';
  const dropZone = useIsoReadZone
    ? document.getElementById('isoOpenDropZone')
    : document.getElementById('homeDropZone');
  if (dropZone) dropZone.classList.toggle('dragover', Boolean(active));
}
window.setNativeDragActive = setNativeDragActive;

function hideArchiveContextMenu() {
  const menu = document.getElementById('archiveContextMenu');
  if (menu) menu.classList.remove('show');
}

function getContextItems() {
  const entry = AppState.contextEntry;
  if (!entry) return [];
  if (AppState.selectedItems.has(entry.fullName)) {
    return Array.from(AppState.selectedItems);
  }
  return [entry.fullName];
}

function showArchiveContextMenu(event, entry) {
  event.preventDefault();
  event.stopPropagation();
  AppState.contextEntry = entry;

  if (!AppState.selectedItems.has(entry.fullName)) {
    AppState.selectedItems.clear();
    AppState.selectedItems.add(entry.fullName);
    renderExplorer();
  }

  const menu = document.getElementById('archiveContextMenu');
  const isZip = AppState.currentArchiveInfo && AppState.currentArchiveInfo.format === 'ZIP';
  document.getElementById('ctxPreviewImage').disabled = entry.isDir || !IMAGE_PREVIEW_PATTERN.test(entry.name);
  document.getElementById('ctxOpenFile').disabled = entry.isDir;
  document.getElementById('ctxMoveOut').disabled = !isZip;
  document.getElementById('ctxDelete').disabled = !isZip;
  document.getElementById('ctxMoveOut').title = isZip ? '' : 'ISO와 기타 형식은 읽기 전용이므로 복사만 가능합니다.';
  document.getElementById('ctxDelete').title = isZip ? '' : 'ISO와 기타 형식은 읽기 전용입니다.';

  menu.classList.add('show');
  const left = Math.min(event.clientX, window.innerWidth - menu.offsetWidth - 8);
  const top = Math.min(event.clientY, window.innerHeight - menu.offsetHeight - 8);
  menu.style.left = `${Math.max(8, left)}px`;
  menu.style.top = `${Math.max(8, top)}px`;
}

function previewContextImage() {
  const entry = AppState.contextEntry;
  hideArchiveContextMenu();
  if (!entry || entry.isDir || !AppState.currentArchiveInfo || !AppState.pyBridge) return;
  showProgress(uiText('그림 미리보기 준비 중...', 'Preparing image preview…'), entry.name);
  AppState.pyBridge.getImagePreview(
    AppState.currentArchiveInfo.file_path,
    entry.fullName,
    AppState.archivePassword || '',
    (resJson) => {
      hideProgress();
      const result = JSON.parse(resJson);
      if (!result.success) {
        alert(uiText('그림 미리보기 실패: ', 'Image preview failed: ') + result.error);
        return;
      }
      document.getElementById('imagePreviewTitle').textContent = result.name;
      document.getElementById('imagePreviewContent').src = result.data_url;
      document.getElementById('imagePreviewMeta').textContent = `${result.width} × ${result.height} · ${formatBytes(result.size)}`;
      document.getElementById('modalImagePreview').classList.add('active');
    }
  );
}

function exportContextItems(moveAfterCopy) {
  hideArchiveContextMenu();
  if (!AppState.currentArchiveInfo || !AppState.pyBridge) return;
  const items = getContextItems();
  if (items.length === 0) return;
  showProgress(moveAfterCopy ? uiText('파일 이동 중...', 'Moving files…') : uiText('파일 복사 중...', 'Copying files…'), items[0]);
  AppState.pyBridge.exportArchiveItems(
    AppState.currentArchiveInfo.file_path,
    JSON.stringify(items),
    moveAfterCopy,
    AppState.archivePassword || '',
    (resJson) => {
      const result = JSON.parse(resJson);
      if (!result.success) {
        hideProgress();
        if (!result.cancelled) alert((moveAfterCopy ? uiText('파일 이동 실패: ', 'Could not move files: ') : uiText('파일 복사 실패: ', 'Could not copy files: ')) + result.error);
        return;
      }
      if (moveAfterCopy) {
        hideProgress();
        openArchiveFile(AppState.currentArchiveInfo.file_path);
      } else {
        finishProgress(uiText(`${result.copied_count}개 파일 복사 완료`, `${result.copied_count} file(s) copied`), result.dest_dir);
      }
    }
  );
}

function deleteContextItems() {
  hideArchiveContextMenu();
  if (!AppState.currentArchiveInfo || !AppState.pyBridge) return;
  const items = getContextItems();
  if (items.length === 0 || !confirm(uiText(`선택한 ${items.length}개 항목을 ZIP에서 삭제하시겠습니까?`, `Delete ${items.length} selected item(s) from the ZIP?`))) return;
  showProgress(uiText('파일 삭제 중...', 'Deleting items…'), items[0]);
  AppState.pyBridge.deleteFilesFromArchive(
    AppState.currentArchiveInfo.file_path,
    JSON.stringify(items),
    (resJson) => {
      hideProgress();
      const result = JSON.parse(resJson);
      if (result.success) openArchiveFile(AppState.currentArchiveInfo.file_path);
      else alert(uiText('파일 삭제 실패: ', 'Could not delete items: ') + result.error);
    }
  );
}

// --------------------------------------------------------------------------
// 1. 아이콘 초기화 (undefined 방지 완벽 보장)
// --------------------------------------------------------------------------
function initIcons() {
  const I = window.CrowIcons;
  if (!I) return;

  const setHtml = (id, svg) => {
    const el = document.getElementById(id);
    if (el && svg) el.innerHTML = svg;
  };

  setHtml('brandCrowLogo', I.logo);
  setHtml('infoCrowLogo', I.logo);

  setHtml('iconToolExtractHere', I.extractHere || I.extract);
  setHtml('iconToolExtractCustom', I.extractCustom || I.folder);
  setHtml('iconToolIsoImage', I.isoDisc);
  setHtml('iconIsoDrop', I.isoDisc);
  setHtml('iconToolPdfOptimize', I.pdfOptimize);
  setHtml('iconToolUpdate', I.update);
  setHtml('iconToolAssociations', I.association);
  setHtml('iconToolAdd', I.addFile);
  setHtml('iconToolDelete', I.delete);
  setHtml('iconToolTest', I.test);
  setHtml('iconToolCodePage', I.codepage);
  setHtml('iconToolCancel', I.cancel);
  setHtml('iconToolInfo', I.info);
  setHtml('iconCardOpen', I.openArchive);
  setHtml('iconCardCompress', I.newArchive);
  setHtml('iconCrumbFolder', I.folder);
  setHtml('iconExplorerSearch', I.search);

  setHtml('iconQuickPdf', I.pdfOptimize);
  setHtml('iconQuickIso', I.isoDisc);
  setHtml('iconQuickConvert', I.convert);
  setHtml('iconQuickBatch', I.batch);
  setHtml('iconQuickCbz', I.cbz);
  setHtml('iconQuickPrivacy', I.privacy);
}

// --------------------------------------------------------------------------
// 2. 전역 플로팅 툴팁 엔진 (마우스 오버 시 메뉴 설명 100% 노출)
// --------------------------------------------------------------------------
function initFloatingTooltips() {
  const tooltipEl = document.getElementById('floatingCrowTooltip');
  if (!tooltipEl) return;

  // Custom tooltip and the browser's delayed native tooltip must not overlap.
  // Preserve the accessible name, then remove native `title` only from elements
  // managed by this tooltip engine.
  document.querySelectorAll('[data-tooltip]').forEach((target) => {
    const text = target.getAttribute('data-tooltip');
    if (text && !target.hasAttribute('aria-label')) {
      target.setAttribute('aria-label', text);
    }
    target.removeAttribute('title');
  });

  document.addEventListener('mouseover', (e) => {
    const target = e.target.closest('[data-tooltip]');
    if (!target) {
      tooltipEl.classList.remove('show');
      return;
    }

    const text = target.getAttribute('data-tooltip');
    if (!text) {
      tooltipEl.classList.remove('show');
      return;
    }

    tooltipEl.textContent = text;
    tooltipEl.classList.add('show');

    const rect = target.getBoundingClientRect();
    const tooltipWidth = tooltipEl.offsetWidth;
    const tooltipHeight = tooltipEl.offsetHeight;

    // 타겟 요소의 아래쪽 중앙에 배치
    let left = rect.left + (rect.width / 2) - (tooltipWidth / 2);
    let top = rect.bottom + 8;

    // 화면 경계 보정
    if (left < 10) left = 10;
    if (left + tooltipWidth > window.innerWidth - 10) {
      left = window.innerWidth - tooltipWidth - 10;
    }

    // 아래쪽 공간이 부족하면 위쪽에 배치
    if (top + tooltipHeight > window.innerHeight - 10) {
      top = rect.top - tooltipHeight - 8;
    }

    tooltipEl.style.left = `${left}px`;
    tooltipEl.style.top = `${top}px`;
  });

  document.addEventListener('mouseout', (e) => {
    const target = e.target.closest('[data-tooltip]');
    if (target) {
      tooltipEl.classList.remove('show');
    }
  });
}

// --------------------------------------------------------------------------
// 3. 뷰 전환 및 툴바 컨텍스트 제어 (Home <-> Explorer)
// --------------------------------------------------------------------------
function showExplorerViewTooltips() {
  if (!AppState.currentArchiveInfo) return;
  const isReadOnly = Boolean(AppState.currentArchiveInfo.is_read_only);
  const isEn = AppState.language === 'en';
  const hereButton = document.getElementById('btnToolExtractHere');
  const customButton = document.getElementById('btnToolExtractCustom');
  const hereLabel = isReadOnly
    ? (isEn ? 'Copy ISO files to current folder' : 'ISO 파일을 현재 폴더로 복사')
    : (isEn ? 'Extract to current folder (smart)' : '현재 폴더에 풀기 (스마트 알아서 풀기)');
  const customLabel = isReadOnly
    ? (isEn ? 'Copy ISO files to chosen folder' : 'ISO 파일을 지정 폴더로 복사')
    : (isEn ? 'Extract to chosen folder' : '폴더 지정하여 풀기');
  hereButton.setAttribute('aria-label', hereLabel);
  hereButton.dataset.tooltip = hereLabel;
  hereButton.removeAttribute('title');
  customButton.setAttribute('aria-label', customLabel);
  customButton.dataset.tooltip = customLabel;
  customButton.removeAttribute('title');
}

function showHomeView() {
  AppState.currentView = 'home';
  AppState.currentArchiveInfo = null;
  AppState.currentDirectory = '';
  AppState.explorerFilter = '';
  const filterInput = document.getElementById('explorerFilterInput');
  if (filterInput) filterInput.value = '';
  AppState.selectedItems.clear();
  hideArchiveContextMenu();
  
  document.getElementById('viewHome').classList.add('active');
  document.getElementById('viewExplorer').classList.remove('active');

  // 초기 화면: 아카이브 조작 툴바 숨김, 홈 툴바 노출
  document.getElementById('navGroupExplorer').style.display = 'none';
  document.getElementById('navGroupHome').style.display = 'flex';
}

function showExplorerView(archiveInfo) {
  AppState.currentView = 'explorer';
  AppState.currentArchiveInfo = archiveInfo;
  AppState.currentDirectory = '';
  AppState.explorerFilter = '';
  const filterInput = document.getElementById('explorerFilterInput');
  if (filterInput) filterInput.value = '';
  AppState.selectedItems = new Set(
    archiveInfo.items
      .map(item => item.name.replace(/\\/g, '/'))
      .filter(name => name && !name.endsWith('/'))
  );
  AppState.selectionAnchorIndex = null;

  document.getElementById('viewHome').classList.remove('active');
  document.getElementById('viewExplorer').classList.add('active');

  // 아카이브 열림: 아카이브 조작 툴바 노출, 홈 툴바 숨김
  document.getElementById('navGroupExplorer').style.display = 'flex';
  document.getElementById('navGroupHome').style.display = 'none';

  const isReadOnly = Boolean(archiveInfo.is_read_only);
  document.getElementById('btnToolAdd').style.display = isReadOnly ? 'none' : '';
  document.getElementById('btnToolDelete').style.display = isReadOnly ? 'none' : '';
  document.getElementById('btnToolCodePage').style.display = isReadOnly ? 'none' : '';
  showExplorerViewTooltips();

  renderExplorer();
}

// --------------------------------------------------------------------------
// 4. 반디집형 아카이브 탐색기 렌더링 & 브레드크럼
// --------------------------------------------------------------------------
function renderExplorer() {
  const info = AppState.currentArchiveInfo;
  if (!info) return;

  // 1. 브레드크럼
  document.getElementById('lblArchiveRootName').textContent = info.filename;
  const subCrumbsEl = document.getElementById('subPathCrumbs');
  subCrumbsEl.innerHTML = '';

  const dirParts = AppState.currentDirectory.split('/').filter(Boolean);
  let accumulatedPath = '';
  dirParts.forEach((part) => {
    accumulatedPath += part + '/';
    const thisPath = accumulatedPath;

    const sep = document.createElement('span');
    sep.className = 'crumb-sep';
    sep.textContent = '>';
    subCrumbsEl.appendChild(sep);

    const crumb = document.createElement('span');
    crumb.className = 'path-crumb';
    crumb.textContent = part;
    crumb.onclick = () => {
      AppState.currentDirectory = thisPath;
      renderExplorer();
    };
    subCrumbsEl.appendChild(crumb);
  });

  // 2. 현재 디렉터리 필터링
  const currentPrefix = AppState.currentDirectory;
  const currentLevelItems = new Map();

  info.items.forEach(item => {
    const itemName = item.name.replace(/\\/g, '/');
    if (!itemName.startsWith(currentPrefix)) return;
    if (itemName === currentPrefix) return;

    const relName = itemName.slice(currentPrefix.length);
    const parts = relName.split('/').filter(Boolean);
    if (parts.length === 0) return;

    const firstSegment = parts[0];
    const isDir = parts.length > 1 || item.is_dir;

    if (!currentLevelItems.has(firstSegment)) {
      currentLevelItems.set(firstSegment, {
        name: firstSegment,
        fullName: currentPrefix + firstSegment + (isDir ? '/' : ''),
        isDir: isDir,
        size: isDir ? 0 : item.size,
        compressedSize: isDir ? 0 : (item.compressed_size || item.size),
        dateTime: item.date_time || '-'
      });
    } else {
      if (!isDir) {
        const existing = currentLevelItems.get(firstSegment);
        existing.size += item.size;
        existing.compressedSize += (item.compressed_size || item.size);
      }
    }
  });

  // 3. 테이블 렌더링
  const tbody = document.getElementById('tblExplorerBody');
  tbody.innerHTML = '';

  if (AppState.currentDirectory !== '') {
    const upRow = document.createElement('tr');
    upRow.innerHTML = `
      <td></td>
      <td colspan="4" class="file-cell" style="color: #38bdf8;">
        <span class="file-icon-svg folder">${window.CrowIcons.folderUp || window.CrowIcons.folder}</span>
        <strong>${AppState.language === 'en' ? '[Parent folder]' : '[상위 폴더]'}</strong>
      </td>
    `;
    upRow.ondblclick = () => {
      const parts = AppState.currentDirectory.split('/').filter(Boolean);
      parts.pop();
      AppState.currentDirectory = parts.length > 0 ? parts.join('/') + '/' : '';
      renderExplorer();
    };
    tbody.appendChild(upRow);
  }

  const filterQuery = (AppState.explorerFilter || '').trim().toLowerCase();
  const sortedItems = Array.from(currentLevelItems.values())
    .filter(item => !filterQuery || item.name.toLowerCase().includes(filterQuery))
    .sort((a, b) => {
      if (a.isDir && !b.isDir) return -1;
      if (!a.isDir && b.isDir) return 1;
      return a.name.localeCompare(b.name);
    });

  const selectionNamesForEntry = (entry) => {
    if (!entry.isDir) return [entry.fullName];
    const children = info.items
      .map(item => item.name.replace(/\\/g, '/'))
      .filter(name => name && !name.endsWith('/') && name.startsWith(entry.fullName));
    return children.length ? children : [entry.fullName];
  };

  const isEntrySelected = (entry) => {
    const names = selectionNamesForEntry(entry);
    return names.length > 0 && names.every(name => AppState.selectedItems.has(name));
  };

  const setEntrySelected = (entry, checked) => {
    selectionNamesForEntry(entry).forEach((name) => {
      if (checked) AppState.selectedItems.add(name);
      else AppState.selectedItems.delete(name);
    });
  };

  const applyVisibleSelection = (index, event, forcedState = null) => {
    const entry = sortedItems[index];
    const desired = forcedState === null ? !isEntrySelected(entry) : Boolean(forcedState);
    if (event && event.shiftKey && AppState.selectionAnchorIndex !== null) {
      const start = Math.min(AppState.selectionAnchorIndex, index);
      const end = Math.max(AppState.selectionAnchorIndex, index);
      for (let cursor = start; cursor <= end; cursor += 1) {
        setEntrySelected(sortedItems[cursor], desired);
      }
    } else {
      setEntrySelected(entry, desired);
    }
    AppState.selectionAnchorIndex = index;
  };

  sortedItems.forEach((entry, index) => {
    const tr = document.createElement('tr');
    tr.dataset.fullName = entry.fullName;
    let dragStarted = false;
    tr.addEventListener('pointerdown', event => {
      if (event.button !== 0 || event.target.tagName === 'INPUT') return;
      event.preventDefault();
      dragStarted = false;
      if (event.isTrusted) tr.setPointerCapture(event.pointerId);
      const start = {x: event.clientX, y: event.clientY};
      const move = e => {
        if (!(e.buttons & 1)) { tr.removeEventListener('pointermove', move); return; }
        if (Math.hypot(e.clientX-start.x, e.clientY-start.y) < 8) return;
        tr.removeEventListener('pointermove', move);
        if (!AppState.pyBridge) return;
        dragStarted = true;
        // Visible directory roots (not the selected leaf set) are the drag payload.
        const roots = isEntrySelected(entry)
          ? sortedItems.filter(isEntrySelected).map(item => item.fullName)
          : [entry.fullName];
        AppState.pyBridge.dragArchiveItems(AppState.currentArchiveInfo.file_path,
          JSON.stringify(roots), AppState.archivePassword || '', result => {
            const response = JSON.parse(result);
            if (!response.success) alert(response.error);
          });
      };
      tr.addEventListener('pointermove', move);
      tr.addEventListener('pointerup', () => tr.removeEventListener('pointermove', move), {once:true});
      tr.addEventListener('pointercancel', () => tr.removeEventListener('pointermove', move), {once:true});
    });

    const isChecked = isEntrySelected(entry);
    const resolveFileIcon = (name) => {
      const I = window.CrowIcons;
      if (IMAGE_PREVIEW_PATTERN.test(name)) return I.fileImage || I.file;
      if (PDF_FILE_PATTERN.test(name)) return I.filePdf || I.file;
      if (ARCHIVE_FILE_PATTERN.test(name)) return I.fileArchive || I.file;
      if (EXEC_FILE_PATTERN.test(name)) return I.fileExec || I.file;
      return I.file;
    };
    const iconSvg = entry.isDir ? window.CrowIcons.folder : resolveFileIcon(entry.name);
    const iconClass = entry.isDir ? 'folder' : '';

    const checkboxCell = document.createElement('td');
    checkboxCell.className = 'check-cell';
    const chk = document.createElement('input');
    chk.type = 'checkbox';
    chk.className = 'item-chk';
    chk.checked = isChecked;
    checkboxCell.appendChild(chk);

    const nameCell = document.createElement('td');
    const fileCell = document.createElement('div');
    fileCell.className = 'file-cell';
    const icon = document.createElement('span');
    icon.className = `file-icon-svg ${iconClass}`;
    icon.innerHTML = iconSvg; // bundled static SVG only
    const name = document.createElement('span');
    name.textContent = entry.name;
    fileCell.append(icon, name);
    nameCell.appendChild(fileCell);

    const originalSizeCell = document.createElement('td');
    originalSizeCell.style.textAlign = 'right';
    originalSizeCell.textContent = entry.isDir ? '-' : formatBytes(entry.size);
    const compressedSizeCell = document.createElement('td');
    compressedSizeCell.style.textAlign = 'right';
    compressedSizeCell.textContent = entry.isDir ? '-' : formatBytes(entry.compressedSize);
    const dateCell = document.createElement('td');
    dateCell.style.textAlign = 'center';
    dateCell.style.color = 'var(--text-muted)';
    dateCell.textContent = String(entry.dateTime);
    tr.append(checkboxCell, nameCell, originalSizeCell, compressedSizeCell, dateCell);
    chk.addEventListener('click', (e) => {
      e.stopPropagation();
      applyVisibleSelection(index, e, chk.checked);
      renderExplorer();
    });

    checkboxCell.addEventListener('click', (e) => {
      e.stopPropagation();
      if (e.target !== chk) {
        applyVisibleSelection(index, e);
        renderExplorer();
      }
    });

    tr.addEventListener('click', (e) => {
      if (dragStarted) { dragStarted = false; return; }
      applyVisibleSelection(index, e);
      renderExplorer();
    });

    tr.addEventListener('mousedown', (e) => {
      if (e.button !== 2) return;
      AppState.rightDragSelecting = true;
      AppState.rightDragMoved = false;
      AppState.rightDragStartName = entry.fullName;
      setEntrySelected(entry, true);
      chk.checked = true;
      AppState.selectionAnchorIndex = index;
      updateExplorerStatusBar();
      tr.classList.add('selected');
    });

    tr.addEventListener('mouseenter', (e) => {
      if (!AppState.rightDragSelecting || !(e.buttons & 2)) return;
      if (entry.fullName !== AppState.rightDragStartName) AppState.rightDragMoved = true;
      setEntrySelected(entry, true);
      tr.classList.add('selected');
      const rowCheckbox = tr.querySelector('.item-chk');
      if (rowCheckbox) rowCheckbox.checked = true;
      updateExplorerStatusBar();
    });

    tr.addEventListener('dblclick', (e) => {
      e.stopPropagation();
      if (entry.isDir) {
        AppState.currentDirectory = entry.fullName;
        renderExplorer();
      } else {
        openFileTemp(entry.fullName);
      }
    });

    tr.addEventListener('contextmenu', (e) => {
      if (AppState.rightDragMoved) {
        e.preventDefault();
        e.stopPropagation();
        AppState.rightDragMoved = false;
        return;
      }
      showArchiveContextMenu(e, entry);
    });

    if (isChecked) tr.classList.add('selected');

    tbody.appendChild(tr);
  });

  updateExplorerStatusBar();
  const selectAll = document.getElementById('chkSelectAll');
  if (selectAll) {
    const visibleSelections = sortedItems.map(isEntrySelected);
    selectAll.checked = visibleSelections.length > 0 && visibleSelections.every(Boolean);
    selectAll.indeterminate = visibleSelections.some(Boolean) && !selectAll.checked;
  }
}

function updateExplorerStatusBar() {
  const info = AppState.currentArchiveInfo;
  if (!info) return;

  const totalFiles = info.file_count;
  const selCount = Array.from(AppState.selectedItems).filter(name => !name.endsWith('/')).length;
  const summaryEl = document.getElementById('statExplorerSummary');
  const sizesEl = document.getElementById('statExplorerSizes');
  const isEn = AppState.language === 'en';

  if (selCount > 0) {
    summaryEl.textContent = isEn
      ? `${selCount} selected (${totalFiles} files total)`
      : `${selCount}개 선택됨 (전체 ${totalFiles}개 파일)`;
  } else {
    summaryEl.textContent = isEn
      ? `${totalFiles} files (${info.dir_count} folders)`
      : `총 ${totalFiles}개 파일 (${info.dir_count}개 폴더)`;
  }

  sizesEl.textContent = isEn
    ? `Original ${formatBytes(info.uncompressed_size)} / Packed ${formatBytes(info.compressed_size || info.archive_size)} (Saved ${info.compression_ratio}%)`
    : `원본 ${formatBytes(info.uncompressed_size)} / 압축 ${formatBytes(info.compressed_size || info.archive_size)} (절감률 ${info.compression_ratio}%)`;
}

// 파일 임시 추출 및 실행
function openFileTemp(itemName) {
  if (!AppState.currentArchiveInfo || !AppState.pyBridge) return;
  showProgress(uiText('파일 여는 중...', 'Opening file…'), itemName);
  AppState.pyBridge.extractSingleAndOpen(AppState.currentArchiveInfo.file_path, itemName, AppState.archivePassword || "", (resJson) => {
    hideProgress();
    const res = JSON.parse(resJson);
    if (!res.success) {
      alert(uiText('파일을 열 수 없습니다: ', 'Could not open the file: ') + res.error);
    }
  });
}

// --------------------------------------------------------------------------
// 5. 드래그 앤 드롭 파일 처리 (새로 압축 리스트 즉시 반영 보장)
// --------------------------------------------------------------------------
function handleDroppedFiles(filePaths) {
  if (!filePaths || filePaths.length === 0) return;

  const isoModal = document.getElementById('modalIsoImage');
  if (isoModal.classList.contains('active')) {
    if (AppState.isoTab === 'read') {
      if (filePaths.length !== 1 || !ISO_PATTERN.test(filePaths[0])) {
        alert(AppState.language === 'en' ? 'Drop one .iso file.' : '.iso 파일 한 개만 끌어다 놓아 주세요.');
        return;
      }
      closeIsoImageModal();
      openArchiveFile(filePaths[0]);
    } else {
      addPathsToIso(filePaths);
    }
    return;
  }

  const firstPath = filePaths[0];
  const isArchive = /\.(zip|alz|egg|7z|rar|tar|gz|tgz|bz2|tbz2|xz|txz|cab|iso)$/i.test(firstPath);

  // 1개 압축 파일 단독 드롭 시 -> 아카이브 열기
  if (isArchive && filePaths.length === 1 && !document.getElementById('modalNewCompress').classList.contains('active')) {
    openArchiveFile(firstPath);
  } else {
    // 복수 파일 또는 일반 폴더 드롭 시 -> 새로압축 리스트 추가 & 모달 오픈
    addPathsToCompress(filePaths);
    openNewCompressModal();
  }
}

window.handleNativeDrop = handleDroppedFiles;
window.handleDroppedFiles = handleDroppedFiles;

function openArchiveFile(filePath) {
  if (!AppState.pyBridge) return;
  showProgress(uiText('아카이브 분석 중...', 'Reading archive…'), filePath.split(/[\\/]/).pop());
  
  const enc = AppState.selectedEncoding === 'auto' ? '' : AppState.selectedEncoding;
  AppState.pyBridge.listArchive(filePath, "", enc, (resJson) => {
    hideProgress();
    const info = JSON.parse(resJson);
    if (info.error) {
      alert(uiText('압축 파일을 열 수 없습니다: ', 'Could not open the archive: ') + info.error);
      showHomeView();
    } else {
      showExplorerView(info);
    }
  });
}

function addPathsToCompress(paths) {
  if (!paths || paths.length === 0) return;
  const currentSet = new Set(AppState.compressSourcePaths);
  paths.forEach(p => currentSet.add(p));
  AppState.compressSourcePaths = Array.from(currentSet);
  renderCompressSourceList();
}

function renderCompressSourceList() {
  const container = document.getElementById('compressFileListPreview');
  const paths = AppState.compressSourcePaths;

  if (paths.length === 0) {
    const message = AppState.language === 'en'
      ? 'Add files or folders, or drop them here.'
      : '압축할 파일이나 폴더를 추가하거나 이곳으로 끌어다 놓으세요.';
    container.innerHTML = `<div style="padding: 10px; text-align: center; color: var(--text-muted);">${message}</div>`;
    return;
  }

  // 1단계: 즉시 동기 렌더링
  container.innerHTML = '';
  const totalInfo = document.createElement('div');
  totalInfo.style.cssText = 'font-weight: 700; color: #c7d2fe; margin-bottom: 6px;';
  totalInfo.id = 'lblCompressTotalInfo';
  totalInfo.textContent = AppState.language === 'en'
    ? `${paths.length} items added (analyzing...)`
    : `총 ${paths.length}개 항목 등록됨 (상세 분석 중...)`;
  container.appendChild(totalInfo);

  paths.forEach((p, idx) => {
    const base = p.split(/[\\/]/).pop();
    const itemDiv = document.createElement('div');
    itemDiv.className = 'drop-file-item';
    const pathLabel = document.createElement('span');
    pathLabel.title = p;
    pathLabel.textContent = `📁 ${base}`;
    const removeButton = document.createElement('button');
    removeButton.style.cssText = 'background:transparent; border:none; color:var(--accent-rose); cursor:pointer; font-size:14px;';
    removeButton.title = '제거';
    removeButton.textContent = '×';
    removeButton.onclick = () => {
      AppState.compressSourcePaths.splice(idx, 1);
      renderCompressSourceList();
    };
    itemDiv.append(pathLabel, removeButton);
    container.appendChild(itemDiv);
  });

  // 2단계: 백엔드 상세 분석
  if (AppState.pyBridge) {
    AppState.pyBridge.getFilesDetails(JSON.stringify(paths), (resJson) => {
      const details = JSON.parse(resJson);
      if (details.success) {
        const lbl = document.getElementById('lblCompressTotalInfo');
        if (lbl) {
          lbl.textContent = AppState.language === 'en'
            ? `${details.file_count} files (${formatBytes(details.total_size)})`
            : `총 ${details.file_count}개 파일 (${formatBytes(details.total_size)})`;
        }
      }
    });
  }
}

function addPathsToIso(paths) {
  if (!paths || paths.length === 0) return;
  const currentSet = new Set(AppState.isoSourcePaths);
  paths.forEach((path) => currentSet.add(path));
  AppState.isoSourcePaths = Array.from(currentSet);
  renderIsoSourceList();
}

function renderIsoSourceList() {
  const container = document.getElementById('isoFileListPreview');
  container.innerHTML = '';

  if (AppState.isoSourcePaths.length === 0) {
    const hint = document.createElement('div');
    hint.className = 'empty-list-hint';
    hint.textContent = AppState.language === 'en'
      ? 'Add files or folders, or drop them here for the ISO.'
      : 'ISO에 넣을 파일이나 폴더를 추가하거나 이곳으로 끌어다 놓으세요.';
    container.appendChild(hint);
    return;
  }

  AppState.isoSourcePaths.forEach((path, index) => {
    const item = document.createElement('div');
    item.className = 'drop-file-item';
    const label = document.createElement('span');
    label.title = path;
    label.textContent = `📁 ${path.split(/[\\/]/).pop()}`;
    const remove = document.createElement('button');
    remove.className = 'source-remove-btn';
    remove.type = 'button';
    remove.title = '제거';
    remove.textContent = '×';
    remove.onclick = () => {
      AppState.isoSourcePaths.splice(index, 1);
      renderIsoSourceList();
    };
    item.append(label, remove);
    container.appendChild(item);
  });
}

// --------------------------------------------------------------------------
// 6. 모달 제어
// --------------------------------------------------------------------------
function openNewCompressModal() {
  document.getElementById('modalNewCompress').classList.add('active');
  renderCompressSourceList();
}
function closeNewCompressModal() {
  document.getElementById('modalNewCompress').classList.remove('active');
  const pwd = document.getElementById('txtCompressPwd');
  const conf = document.getElementById('passwordConfirm');
  const showBtn = document.getElementById('passwordShow');
  if (pwd) pwd.type = 'password';
  if (conf) conf.type = 'password';
  if (showBtn) showBtn.textContent = AppState.language === 'en' ? 'Show' : '표시';
}

function setIsoTab(tabName) {
  AppState.isoTab = tabName === 'create' ? 'create' : 'read';
  const isRead = AppState.isoTab === 'read';
  document.getElementById('btnIsoTabRead').classList.toggle('active', isRead);
  document.getElementById('btnIsoTabRead').setAttribute('aria-selected', String(isRead));
  document.getElementById('btnIsoTabCreate').classList.toggle('active', !isRead);
  document.getElementById('btnIsoTabCreate').setAttribute('aria-selected', String(!isRead));
  document.getElementById('isoReadPanel').hidden = !isRead;
  document.getElementById('isoReadPanel').classList.toggle('active', isRead);
  document.getElementById('isoCreatePanel').hidden = isRead;
  document.getElementById('isoCreatePanel').classList.toggle('active', !isRead);
  document.getElementById('btnCreateIso').hidden = isRead;
  setNativeDragActive(false);
  if (!isRead) renderIsoSourceList();
}

function openIsoImageModal() {
  document.getElementById('modalIsoImage').classList.add('active');
  setIsoTab('read');
}

function closeIsoImageModal() {
  document.getElementById('modalIsoImage').classList.remove('active');
  setNativeDragActive(false);
}

function openPdfOptimizeModal() {
  document.getElementById('modalPdfOptimize').classList.add('active');
}
function closePdfOptimizeModal() {
  document.getElementById('modalPdfOptimize').classList.remove('active');
}

function renderPdfAnalysis(analysis, selectRecommendation = true) {
  AppState.pdfAnalysis = analysis;
  AppState.pdfInputPath = analysis.input_path || '';
  const composition = analysis.composition || {};
  const typeLabels = {
    scan_or_photo: uiText('스캔·사진 중심', 'Scans and photos'),
    office_document: uiText('Office·폰트 중심', 'Office document and fonts'),
    text_or_vector: uiText('텍스트·벡터 중심', 'Text and vectors'),
    encrypted: uiText('암호화 문서', 'Encrypted document')
  };
  const option = Array.from(document.querySelectorAll('input[name="pdfPreset"]'))
    .find(input => input.value === analysis.recommendation);
  const presetLabel = option?.closest('label')?.querySelector('.pdf-preset-title')?.textContent
    || uiText('처리 불가', 'Unavailable');
  document.getElementById('pdfAnalysisSummary').textContent = [
    analysis.filename,
    uiText(analysis.page_count + '쪽', analysis.page_count + (analysis.page_count === 1 ? ' page' : ' pages')),
    formatBytes(analysis.original_size),
    typeLabels[analysis.document_type] ?? '',
    uiText(
      '이미지 ' + (composition.images || 0) + '% / 폰트 ' + (composition.fonts || 0) + '% / 첨부 ' + (composition.attachments || 0) + '%',
      'Images ' + (composition.images || 0) + '% / Fonts ' + (composition.fonts || 0) + '% / Attachments ' + (composition.attachments || 0) + '%'
    ),
    uiText('권장: ', 'Recommended: ') + presetLabel
  ].filter(Boolean).join(' · ');
  if (selectRecommendation && option) option.checked = true;
}

function refreshEncodingTooltip() {
  const labels = {
    auto: uiText('자동 감지', 'Auto detect'),
    cp949: uiText('한국어 (CP949)', 'Korean (CP949)'),
    'utf-8': 'UTF-8',
    shift_jis: uiText('일본어 (SJIS)', 'Japanese (SJIS)'),
    gbk: uiText('중국어 (GBK)', 'Chinese (GBK)'),
    raw: uiText('원본 (Raw)', 'Raw')
  };
  const button = document.getElementById('btnToolCodePage');
  const label = uiText('코드페이지: ', 'Encoding: ') + (labels[AppState.selectedEncoding] || labels.auto);
  button.setAttribute('data-tooltip', label);
  button.setAttribute('aria-label', label);
  button.removeAttribute('title');
}

function openCodePageModal() {
  document.getElementById('modalCodePage').classList.add('active');
}
function closeCodePageModal() {
  document.getElementById('modalCodePage').classList.remove('active');
}

function openInfoModal() {
  document.getElementById('modalInfoApp').classList.add('active');
}
function closeInfoModal() {
  document.getElementById('modalInfoApp').classList.remove('active');
}

function showProgress(title, currentFile = uiText('준비 중...', 'Preparing…')) {
  const modal = document.getElementById('modalProgress');
  document.getElementById('progressTitleText').textContent = title;
  document.getElementById('progressFileText').textContent = currentFile;
  document.getElementById('progressBarInner').style.width = '0%';
  document.getElementById('progressPercentLbl').textContent = '0%';
  document.getElementById('progressDoneBtns').style.display = 'none';
  modal.classList.add('active');
}

function updateProgress(current, total, filename) {
  const percent = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
  document.getElementById('progressBarInner').style.width = `${percent}%`;
  document.getElementById('progressPercentLbl').textContent = `${percent}% (${current}/${total})`;
  if (filename) document.getElementById('progressFileText').textContent = filename;
}

function finishProgress(msg, folderPath = null) {
  AppState.lastExtractedFolder = folderPath;
  document.getElementById('progressBarInner').style.width = '100%';
  document.getElementById('progressPercentLbl').textContent = uiText('100% 완료', '100% complete');
  document.getElementById('progressTitleText').textContent = uiText('작업 완료!', 'Done');
  document.getElementById('progressFileText').textContent = msg;
  document.getElementById('progressDoneBtns').style.display = 'flex';
}

function hideProgress() {
  document.getElementById('modalProgress').classList.remove('active');
}

// --------------------------------------------------------------------------
// 7. PySide6 Native WebChannel 브릿지 연동
// --------------------------------------------------------------------------
function initNativeBridge() {
  if (typeof QWebChannel !== 'undefined') {
    new QWebChannel(qt.webChannelTransport, (channel) => {
      AppState.pyBridge = channel.objects.coreBridge;
      AppState.pyBridge.setUiLanguage(AppState.language);
      if (AppState.pyBridge.dragStatus) AppState.pyBridge.dragStatus.connect(message => {
        const status = document.getElementById('statExplorerSummary');
        if (status) status.textContent = message;
      });
      console.log('PySide6 Native Bridge Connected (CrowPack v1.7)!');

      AppState.pyBridge.progressEvent.connect((current, total, file) => {
        updateProgress(current, total, file);
      });

    });
  }
}

// --------------------------------------------------------------------------
// 8. 전체 버튼 및 이벤트 바인딩
// --------------------------------------------------------------------------
function initEvents() {
  // 브랜드 클릭 시 홈으로
  document.getElementById('btnBrandHome').onclick = showHomeView;
  document.getElementById('crumbRoot').onclick = () => {
    AppState.currentDirectory = '';
    renderExplorer();
  };

  // 초기 화면 카드
  document.getElementById('btnCardOpenArchive').onclick = () => {
    if (AppState.pyBridge) {
      AppState.pyBridge.selectArchiveFile((filePath) => {
        if (filePath) openArchiveFile(filePath);
      });
    }
  };

  document.getElementById('btnCardNewCompress').onclick = () => {
    openNewCompressModal();
  };

  document.getElementById('btnToolIsoImage').onclick = openIsoImageModal;
  document.getElementById('btnIsoSelectFile').onclick = () => {
    if (AppState.pyBridge) {
      AppState.pyBridge.selectIsoFile((filePath) => {
        if (filePath) {
          closeIsoImageModal();
          openArchiveFile(filePath);
        }
      });
    }
  };
  document.getElementById('btnIsoTabRead').onclick = () => setIsoTab('read');
  document.getElementById('btnIsoTabCreate').onclick = () => setIsoTab('create');
  document.getElementById('btnCloseIsoImage').onclick = closeIsoImageModal;
  document.getElementById('btnCancelIsoImage').onclick = closeIsoImageModal;

  document.getElementById('btnToolPdfOptimize').onclick = openPdfOptimizeModal;
  document.getElementById('btnClosePdfOptimize').onclick = closePdfOptimizeModal;
  document.getElementById('btnCancelPdfOptimize').onclick = closePdfOptimizeModal;
  document.getElementById('btnAnalyzePdf').onclick = () => {
    if (!AppState.pyBridge) return;
    AppState.pyBridge.analyzePdf((resJson) => {
      const result = JSON.parse(resJson);
      if (result.success) renderPdfAnalysis(result);
      else if (!result.cancelled) alert(uiText('PDF 분석 실패: ', 'PDF analysis failed: ') + result.error);
    });
  };
  document.getElementById('btnRunPdfOptimize').onclick = () => {
    const selected = document.querySelector('input[name="pdfPreset"]:checked');
    const preset = selected ? selected.value : 'balanced';
    if (!AppState.pyBridge) return;
    if (preset === 'extreme' && !confirm(
      uiText('극한 압축은 페이지를 이미지로 다시 만들어 텍스트 선택, 링크, 양식, 주석과 벡터 구조가 사라질 수 있습니다. 계속하시겠습니까?', 'Extreme optimization converts pages to images. Selectable text, links, forms, annotations, and vector content may be lost. Continue?')
    )) return;
    closePdfOptimizeModal();
    showProgress(uiText('PDF 용량 줄이는 중...', 'Optimizing PDF…'), uiText('원본을 보호하며 새 PDF로 저장합니다.', 'Saving a separate PDF and preserving the original.'));
    const callback = (resJson) => {
      const result = JSON.parse(resJson);
      if (!result.success) {
        hideProgress();
        if (!result.cancelled) alert(uiText('PDF 최적화 실패: ', 'PDF optimization failed: ') + result.error);
        return;
      }
      if (!result.output_path) {
        hideProgress();
        alert(uiText(
          `${result.message}\n처리 이미지 ${result.images_processed || 0}개 / 제외 ${result.images_skipped || 0}개`,
          `The selected preset did not reduce file size. The original was kept.\nImages processed: ${result.images_processed || 0} / skipped: ${result.images_skipped || 0}`
        ));
        return;
      }
      finishProgress(
        uiText(`${result.message} · ${result.compression_ratio}% 감소 · ${formatBytes(result.saved_bytes)} 절감`,
          `PDF optimized · ${result.compression_ratio}% smaller · ${formatBytes(result.saved_bytes)} saved`) +
        (result.images_processed ? uiText(` · 이미지 ${result.images_processed}개 처리`, ` · Images processed: ${result.images_processed}`) : '') +
        (result.pages_rasterized ? uiText(` · ${result.pages_rasterized}쪽 재구성`, ` · Pages rasterized: ${result.pages_rasterized}`) : ''),
        result.output_dir
      );
    };
    if (AppState.pdfInputPath) AppState.pyBridge.optimizePdfFile(preset, AppState.pdfInputPath, callback);
    else AppState.pyBridge.optimizePdfPreset(preset, callback);
  };

  document.getElementById('btnToolUpdate').onclick = () => {
    if (!AppState.pyBridge) return;
    AppState.pyBridge.checkForUpdates((resJson) => {
      const result = JSON.parse(resJson);
      if (result.success) {
        alert(`CrowPack v${result.version}\n${result.message}`);
      } else {
        alert(`업데이트 확인 실패\n${result.error}`);
      }
    });
  };

  document.getElementById('btnToolAssociations').onclick = () => {
    if (!AppState.pyBridge) return;
    AppState.pyBridge.registerFileAssociations((resJson) => {
      const result = JSON.parse(resJson);
      if (result.success) alert(result.message);
      else alert(uiText('확장자 연결 등록 실패: ', 'Could not register file associations: ') + result.error);
    });
  };

  // [취소 / 닫기 버튼]
  document.getElementById('btnToolCancel').onclick = () => {
    showHomeView();
  };

  // [이 폴더에 풀기]
  document.getElementById('btnToolExtractHere').onclick = () => {
    triggerExtract(true);
  };

  // [폴더변경 풀기]
  document.getElementById('btnToolExtractCustom').onclick = () => {
    triggerExtract(false);
  };

  function triggerExtract(useDefaultDir) {
    if (!AppState.currentArchiveInfo) return;

    const archivePath = AppState.currentArchiveInfo.file_path;
    const selItems = Array.from(AppState.selectedItems);
    const selJson = selItems.length > 0 ? JSON.stringify(selItems) : "";

    const isReadOnly = Boolean(AppState.currentArchiveInfo.is_read_only);
    showProgress(
      isReadOnly ? uiText('ISO 파일 복사 중...', 'Copying ISO files…') : uiText('스마트 압축 풀기 중...', 'Extracting archive…'),
      useDefaultDir ? uiText('현재 폴더로 처리 중...', 'Using the current folder…') : uiText('지정된 폴더로 처리 중...', 'Using the selected folder…')
    );

    if (AppState.pyBridge) {
      AppState.pyBridge.extractArchiveWithOption(archivePath, "smart", useDefaultDir, selJson, AppState.archivePassword || "", (resJson) => {
        const res = JSON.parse(resJson);
        if (res.success) {
          finishProgress(uiText(`${res.extracted_count}개 파일 ${isReadOnly ? '복사' : '해제'} 완료`, `${res.extracted_count} file(s) ${isReadOnly ? 'copied' : 'extracted'}`), res.dest_dir);
        } else {
          hideProgress();
          if (!res.cancelled && res.error) {
            alert((isReadOnly ? uiText('ISO 파일 복사 실패: ', 'Could not copy ISO files: ') : uiText('압축 해제 실패: ', 'Extraction failed: ')) + res.error);
          }
        }
      });
    }
  }

  // [테스트]
  document.getElementById('btnToolTest').onclick = () => {
    if (!AppState.currentArchiveInfo || !AppState.pyBridge) return;
    showProgress(uiText('무결성 검사 중...', 'Checking archive integrity…'), uiText('손상 여부를 테스트하고 있습니다.', 'Checking for archive damage.'));
    AppState.pyBridge.testArchive(AppState.currentArchiveInfo.file_path, AppState.archivePassword || "", (resJson) => {
      hideProgress();
      const res = JSON.parse(resJson);
      if (res.success) {
        alert(uiText('✅ 무결성 검사 완료: 아카이브에 손상이 없으며 정상입니다.', 'Archive integrity check passed.'));
      } else {
        alert(uiText('❌ 아카이브 손상 감지: ', 'Archive integrity check failed: ') + res.error);
      }
    });
  };

  // [추가]
  document.getElementById('btnToolAdd').onclick = () => {
    if (!AppState.currentArchiveInfo || !AppState.pyBridge) return;
    AppState.pyBridge.selectSourceFiles((pathsJson) => {
      const paths = JSON.parse(pathsJson);
      if (paths && paths.length > 0) {
        showProgress(uiText('파일 추가 중...', 'Adding files…'), uiText('아카이브를 갱신하고 있습니다.', 'Updating archive.'));
        AppState.pyBridge.addFilesToArchive(AppState.currentArchiveInfo.file_path, pathsJson, (resJson) => {
          hideProgress();
          const res = JSON.parse(resJson);
          if (res.success) {
            openArchiveFile(AppState.currentArchiveInfo.file_path);
          } else {
            alert(uiText('파일 추가 실패: ', 'Could not add files: ') + res.error);
          }
        });
      }
    });
  };

  // [삭제]
  document.getElementById('btnToolDelete').onclick = () => {
    if (!AppState.currentArchiveInfo || !AppState.pyBridge) return;
    const selItems = Array.from(AppState.selectedItems);
    if (selItems.length === 0) {
      alert(uiText('삭제할 파일을 먼저 체크박스로 선택해주세요.', 'Select the files to delete first.'));
      return;
    }
    if (!confirm(uiText(`선택한 ${selItems.length}개 항목을 아카이브에서 삭제하시겠습니까?`, `Delete ${selItems.length} selected item(s) from the archive?`))) return;

    showProgress(uiText('파일 삭제 중...', 'Deleting items…'), uiText('아카이브를 갱신하고 있습니다.', 'Updating archive.'));
    AppState.pyBridge.deleteFilesFromArchive(AppState.currentArchiveInfo.file_path, JSON.stringify(selItems), (resJson) => {
      hideProgress();
      const res = JSON.parse(resJson);
      if (res.success) {
        openArchiveFile(AppState.currentArchiveInfo.file_path);
      } else {
        alert(uiText('파일 삭제 실패: ', 'Could not delete items: ') + res.error);
      }
    });
  };

  // [코드페이지 모달]
  document.getElementById('btnToolCodePage').onclick = openCodePageModal;
  document.getElementById('btnCloseCodePage').onclick = closeCodePageModal;
  const btnCancelCodePage = document.getElementById('btnCancelCodePage');
  if (btnCancelCodePage) btnCancelCodePage.onclick = closeCodePageModal;
  document.getElementById('btnApplyCodePage').onclick = () => {
    const checkedRad = document.querySelector('input[name="radEncoding"]:checked');
    if (checkedRad) {
      AppState.selectedEncoding = checkedRad.value;
      refreshEncodingTooltip();
      closeCodePageModal();

      if (AppState.currentArchiveInfo) {
        openArchiveFile(AppState.currentArchiveInfo.file_path);
      }
    }
  };

  // [정보 & 설정 모달]
  document.getElementById('btnToolInfo').onclick = openInfoModal;
  document.getElementById('btnCloseInfoModal').onclick = closeInfoModal;
  document.getElementById('btnConfirmInfo').onclick = closeInfoModal;
  document.getElementById('selAppLanguage').onchange = (event) => applyLanguage(event.target.value);
  document.querySelectorAll('input[name="appTheme"]').forEach((radio) => {
    radio.onchange = () => {
      if (radio.checked) applyTheme(radio.value);
    };
  });

  document.getElementById('btnCloseImagePreview').onclick = () => {
    document.getElementById('modalImagePreview').classList.remove('active');
    document.getElementById('imagePreviewContent').removeAttribute('src');
  };

  document.getElementById('ctxPreviewImage').onclick = previewContextImage;
  document.getElementById('ctxOpenFile').onclick = () => {
    const entry = AppState.contextEntry;
    hideArchiveContextMenu();
    if (entry && !entry.isDir) openFileTemp(entry.fullName);
  };
  document.getElementById('ctxCopyOut').onclick = () => exportContextItems(false);
  document.getElementById('ctxMoveOut').onclick = () => exportContextItems(true);
  document.getElementById('ctxDelete').onclick = deleteContextItems;

  // 새로 압축 모달 버튼들
  document.getElementById('btnCloseNewCompress').onclick = closeNewCompressModal;
  document.getElementById('btnCancelCompress').onclick = closeNewCompressModal;

  document.getElementById('btnAddSourceFiles').onclick = () => {
    if (AppState.pyBridge) {
      AppState.pyBridge.selectSourceFiles((pathsJson) => {
        const paths = JSON.parse(pathsJson);
        addPathsToCompress(paths);
      });
    }
  };

  document.getElementById('btnAddSourceFolder').onclick = () => {
    if (AppState.pyBridge) {
      AppState.pyBridge.selectSourceFolder((pathsJson) => {
        const paths = JSON.parse(pathsJson);
        addPathsToCompress(paths);
      });
    }
  };

  document.getElementById('btnClearSourceList').onclick = () => {
    AppState.compressSourcePaths = [];
    renderCompressSourceList();
  };

  // ISO 만들기 탭
  document.getElementById('btnIsoAddFiles').onclick = () => {
    if (!AppState.pyBridge) return;
    AppState.pyBridge.selectSourceFiles((pathsJson) => addPathsToIso(JSON.parse(pathsJson)));
  };
  document.getElementById('btnIsoAddFolder').onclick = () => {
    if (!AppState.pyBridge) return;
    AppState.pyBridge.selectSourceFolder((pathsJson) => addPathsToIso(JSON.parse(pathsJson)));
  };
  document.getElementById('btnIsoClear').onclick = () => {
    AppState.isoSourcePaths = [];
    renderIsoSourceList();
  };
  document.getElementById('btnCreateIso').onclick = () => {
    if (!AppState.pyBridge || AppState.isoSourcePaths.length === 0) {
      alert(uiText('ISO에 넣을 파일이나 폴더를 추가해주세요.', 'Add files or folders to the ISO.'));
      return;
    }
    const volumeLabel = document.getElementById('txtIsoVolumeLabel').value.trim() || 'CROW_PACK';
    closeIsoImageModal();
    showProgress(uiText('ISO 이미지 만드는 중...', 'Creating ISO image…'), uiText('파일 구조를 기록하고 있습니다.', 'Writing the file structure.'));
    AppState.pyBridge.createIsoImage(
      JSON.stringify(AppState.isoSourcePaths),
      volumeLabel,
      (resJson) => {
        const result = JSON.parse(resJson);
        if (result.success) {
          finishProgress(uiText(`ISO 생성 완료: ${result.output_path}`, `ISO created: ${result.output_path}`), result.output_dir);
        } else {
          hideProgress();
          if (!result.cancelled) alert(uiText('ISO 생성 실패: ', 'ISO creation failed: ') + result.error);
        }
      }
    );
  };

  document.getElementById('selPresetMode').onchange = (e) => {
    const val = e.target.value;
    const selFmt = document.getElementById('selCompressFmt');
    if (val === 'windows' || val === 'macos') selFmt.value = 'ZIP';
    else if (val === 'linux') selFmt.value = 'TAR.GZ';
    else if (val === 'ultra7z') selFmt.value = '7Z';
    const secMode = document.getElementById('securityMode');
    if (secMode && secMode.value === 'private' && selFmt.value !== '7Z') {
      secMode.value = selFmt.value === 'ZIP' ? 'zip' : 'none';
      secMode.dispatchEvent(new Event('change'));
    } else if (secMode && secMode.value === 'zip' && selFmt.value !== 'ZIP') {
      secMode.value = selFmt.value === '7Z' ? 'private' : 'none';
      secMode.dispatchEvent(new Event('change'));
    }
  };

  document.getElementById('selCompressFmt').onchange = (e) => {
    const fmt = e.target.value;
    const secMode = document.getElementById('securityMode');
    if (!secMode) return;
    if (secMode.value === 'private' && fmt !== '7Z') {
      secMode.value = fmt === 'ZIP' ? 'zip' : 'none';
      secMode.dispatchEvent(new Event('change'));
    } else if (secMode.value === 'zip' && fmt !== 'ZIP') {
      secMode.value = fmt === '7Z' ? 'private' : 'none';
      secMode.dispatchEvent(new Event('change'));
    }
  };

  // 홈 빠른 도구(1-Click) 독 & 포맷 뱃지 & 공식 링크
  document.getElementById('btnQuickPdf').onclick = openPdfOptimizeModal;
  document.getElementById('btnQuickIso').onclick = openIsoImageModal;
  document.getElementById('btnQuickConvert').onclick = () => window.openPackTools && window.openPackTools([], 'convert');
  document.getElementById('btnQuickBatch').onclick = () => window.openPackTools && window.openPackTools([], 'batch');
  document.getElementById('btnQuickCbz').onclick = () => window.openPackTools && window.openPackTools([], 'cbz');
  document.getElementById('btnQuickPrivacy').onclick = () => window.openPackTools && window.openPackTools([], 'privacy');

  document.querySelectorAll('#formatBadgesRow .fmt-badge').forEach((badge) => {
    badge.onclick = () => {
      const tip = (FORMAT_TOOLTIPS[AppState.language] || FORMAT_TOOLTIPS.ko)[badge.dataset.fmt];
      if (tip) showToast(tip);
    };
  });

  document.querySelectorAll('[data-link]').forEach((btn) => {
    btn.onclick = () => openOfficialLink(btn.dataset.link);
  });

  const explorerFilterInput = document.getElementById('explorerFilterInput');
  if (explorerFilterInput) {
    explorerFilterInput.oninput = (e) => {
      AppState.explorerFilter = e.target.value || '';
      renderExplorer();
    };
  }

  // 홈 카드 키보드 접근성 (Enter / Space)
  ['btnCardOpenArchive', 'btnCardNewCompress'].forEach((id) => {
    const card = document.getElementById(id);
    if (card) {
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          card.click();
        }
      });
    }
  });

  document.getElementById('btnCompressHere').onclick = () => {
    triggerCompress(false);
  };

  document.getElementById('btnCompressCustom').onclick = () => {
    triggerCompress(true);
  };

  function triggerCompress(changeFolder) {
    if (window.validateSecurity && !window.validateSecurity()) return;
    if (AppState.compressSourcePaths.length === 0) {
      alert(uiText('압축할 파일이나 폴더를 추가해주세요.', 'Add files or folders to compress.'));
      return;
    }

    const fmt = document.getElementById('selCompressFmt').value;
    const preset = document.getElementById('selPresetMode').value;
    const level = parseInt(document.getElementById('selCompressLevel').value, 10);
    const pwd = document.getElementById('txtCompressPwd').value;
    const splitMb = parseInt(document.getElementById('selSplitSize').value, 10);

    closeNewCompressModal();
    showProgress(uiText('압축 파일 생성 중...', 'Creating archive…'), uiText('시스템별 최적화 압축을 진행하고 있습니다.', 'Compressing files with the selected settings.'));

    if (AppState.pyBridge) {
      AppState.pyBridge.createArchiveWithOption(
        JSON.stringify(AppState.compressSourcePaths),
        fmt,
        preset,
        level,
        pwd,
        splitMb,
        changeFolder,
        (resJson) => {
          const res = JSON.parse(resJson);
          if (res.success) {
            finishProgress(uiText(`아카이브 생성 완료: ${res.output_path}`, `Archive created: ${res.output_path}`), res.output_dir);
            if (pwd) document.getElementById('progressFileText').textContent = uiText('비밀번호는 압축파일과 다른 전달 수단으로 전달하세요.', 'Share the password separately from the archive.');
            document.getElementById('txtCompressPwd').value = '';
            if (document.getElementById('passwordConfirm')) document.getElementById('passwordConfirm').value = '';
          } else {
            hideProgress();
            if (!res.cancelled && res.error) {
              alert(uiText('압축 생성 실패: ', 'Archive creation failed: ') + res.error);
            }
          }
        }
      );
    }
  }

  document.getElementById('btnProgressOpenFolder').onclick = () => {
    if (AppState.lastExtractedFolder && AppState.pyBridge) {
      AppState.pyBridge.openFolder(AppState.lastExtractedFolder);
    }
  };
  document.getElementById('btnProgressClose').onclick = hideProgress;

  document.getElementById('chkSelectAll').onchange = (e) => {
    const isChecked = e.target.checked;
    const info = AppState.currentArchiveInfo;
    if (!info) return;
    info.items.forEach((item) => {
      const name = item.name.replace(/\\/g, '/');
      if (!name || name.endsWith('/')) return;
      if (isChecked) AppState.selectedItems.add(name);
      else AppState.selectedItems.delete(name);
    });
    AppState.selectionAnchorIndex = null;
    renderExplorer();
  };

  window.addEventListener('mouseup', (e) => {
    if (e.button !== 2) return;
    AppState.rightDragSelecting = false;
    AppState.rightDragStartName = '';
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('#archiveContextMenu')) hideArchiveContextMenu();
  });
  document.addEventListener('contextmenu', (e) => {
    if (!e.target.closest('#tblExplorerBody tr')) e.preventDefault();
  });
  window.addEventListener('blur', hideArchiveContextMenu);
  window.addEventListener('resize', hideArchiveContextMenu);
  document.getElementById('explorerGridContainer').addEventListener('scroll', hideArchiveContextMenu);

  // 전역 키보드 단축키 (Esc 모달/메뉴 닫기, 탐색기 Ctrl+A / Ctrl+F / Backspace)
  document.addEventListener('keydown', (e) => {
    if (document.getElementById('packWindowsSetup')?.open) return;
    if (e.key === 'Escape') {
      const ctx = document.getElementById('archiveContextMenu');
      if (ctx && ctx.classList.contains('show')) {
        hideArchiveContextMenu();
        return;
      }
      const modals = Array.from(document.querySelectorAll('.layer-modal-backdrop.active'));
      if (modals.length > 0) {
        const top = modals[modals.length - 1];
        if (top.id === 'modalProgress' && document.getElementById('progressDoneBtns').style.display === 'none') return;
        if (top.id === 'modalNewCompress') closeNewCompressModal();
        else if (top.id === 'modalIsoImage') closeIsoImageModal();
        else top.classList.remove('active');
        return;
      }
    }

    if (AppState.currentView !== 'explorer') return;
    if (document.querySelector('.layer-modal-backdrop.active')) return;

    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') {
      const input = document.getElementById('explorerFilterInput');
      if (input) {
        e.preventDefault();
        input.focus();
        input.select();
      }
      return;
    }

    if (document.activeElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
      return;
    }

    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'a') {
      e.preventDefault();
      const chkAll = document.getElementById('chkSelectAll');
      if (chkAll) {
        chkAll.checked = true;
        chkAll.dispatchEvent(new Event('change'));
      }
    } else if (e.key === 'Backspace' && AppState.currentDirectory !== '') {
      e.preventDefault();
      const parts = AppState.currentDirectory.split('/').filter(Boolean);
      parts.pop();
      AppState.currentDirectory = parts.length > 0 ? parts.join('/') + '/' : '';
      renderExplorer();
    }
  });

  // HTML5 Drag & Drop 이벤트 리스너
  window.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    setNativeDragActive(true);
  });

  window.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    setNativeDragActive(false);
  });

  window.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    setNativeDragActive(false);

    // 전체 로컬 경로는 Qt 뷰의 네이티브 dropEvent에서 한 번만 전달한다.
  });
}

// --------------------------------------------------------------------------
// 9. 진입점
// --------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initIcons();
  applyTheme(loadPreference('theme', 'dark'));
  applyLanguage(loadPreference('language', 'ko'));
  initFloatingTooltips();
  initEvents();
  initNativeBridge();
  showHomeView();
});

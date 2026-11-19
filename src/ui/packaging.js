/* v1.7 packaging UI. All filesystem actions go through the native bridge. */
const packText = (ko, en) => AppState.language === 'en' ? en : ko;
let toolPaths = [];
let lastToolText = '';
let manualUpdateCheck = false;
let isPackagedDistribution = null;
let lastUpdateResult = null;
let windowsAssociations = null;

function refreshPackPaths() {
  const el = document.getElementById('packPaths');
  if (!el) return;
  if (toolPaths.length === 0) {
    el.classList.add('is-empty');
    el.textContent = packText(
      '파일이나 폴더를 추가하거나 이곳으로 끌어다 놓으세요.',
      'Add files or folders, or drop them here.'
    );
  } else {
    el.classList.remove('is-empty');
    el.textContent = toolPaths.join('\n');
  }
}

function addPathsToPackTools(paths) {
  if (!paths || !paths.length) return;
  const set = new Set(toolPaths);
  paths.forEach((p) => { if (p) set.add(p); });
  toolPaths = Array.from(set);
  refreshPackPaths();
}

function renderWindowsAssociations() {
  const summary = document.getElementById('packAssociations');
  const list = document.getElementById('packAssociationList');
  if (!summary || !list) return;
  if (!windowsAssociations) {
    summary.textContent = packText('현재 연결 상태 확인 중', 'Checking current file associations');
    return;
  }
  const count = windowsAssociations.filter(row => row.is_crowpack).length;
  summary.textContent = packText(`${windowsAssociations.length}개 중 ${count}개가 현재 CrowPack에 연결됨`,
    `${count} of ${windowsAssociations.length} types use this CrowPack installation`);
  list.replaceChildren(...windowsAssociations.map(row => {
    const item = document.createElement('li');
    const extension = document.createElement('strong');
    extension.textContent = row.extension;
    const status = document.createElement('span');
    status.textContent = row.is_crowpack ? 'CrowPack' : row.assigned
      ? row.handler || packText('다른 앱에 연결됨', 'Assigned to another app')
      : packText('기본 앱 없음', 'No default app');
    if (!row.is_crowpack && row.handler?.replace(/\s/g, '').toLowerCase() === 'crowpack') {
      status.textContent = packText('다른 CrowPack 설치본', 'Another CrowPack installation');
    }
    item.append(extension, status);
    return item;
  }));
}

function refreshWindowsAssociations() {
  AppState.pyBridge?.integrationStatus(raw => {
    windowsAssociations = JSON.parse(raw);
    renderWindowsAssociations();
  });
}

function openWindowsSetup() {
  const dialog = document.getElementById('packWindowsSetup');
  if (!dialog.open) dialog.showModal();
  refreshWindowsAssociations();
}

window.applyPackLanguage = () => {
  const isEn = AppState.language === 'en';
  const text = {
    '#packTools .modal-title': ['도구', 'Tools'],
    '#packSettings .modal-title': ['설정', 'Settings'],
    '#packSelect': ['파일 선택', 'Select files'],
    '#packFolder': ['폴더 추가', 'Add folder'],
    '#packClear': ['비우기', 'Clear'],
    '#packRun': ['실행', 'Run'],
    '#packCopy': ['결과 복사', 'Copy result'],
    '#packDefaults': ['Windows 설정', 'Windows setup'],
    '#packWindowsSetupTitle': ['CrowPack Windows 설정', 'CrowPack Windows setup'],
    '#packWindowsSetupIntro': ['파일 형식별 기본 앱을 확인하세요. 연결 변경은 Windows 설정에서 선택할 수 있습니다.', 'Review the default app for each file type. Choose any changes in Windows Settings.'],
    '#packOpenDefaultApps': ['기본 앱 설정 열기', 'Open default app settings'],
    '#packCreateShortcut': ['바탕화면 바로가기 만들기', 'Create desktop shortcut'],
    '#packFinishWindowsSetup': ['닫기', 'Close'],
    '#packShellOn': ['사용', 'Enable'],
    '#packShellOff': ['해제', 'Disable'],
    '#btnToolUpdate': ['업데이트 확인', 'Check for updates'],
    '#packSectionDisplayTitle': ['화면', 'Display'],
    '#packSectionWindowsTitle': ['Windows 연결', 'Windows Integration'],
    '#packSectionUpdateTitle': ['업데이트', 'Updates'],
    '#packAssocTitle': ['압축 파일 기본 앱', 'Default archive apps'],
    '#packShellTitle': ['탐색기 우클릭 메뉴', 'Explorer context menu'],
    '#packShellDesc': ['압축 및 해제 명령을 표시합니다.', 'Show compress and extract commands.'],
    '#packMode option[value="new_folder"]': ['각각 별도 폴더', 'Separate folders'],
    '#packMode option[value="current"]': ['현재 폴더', 'Current folder'],
    '#packMode option[value="smart"]': ['알아서 풀기', 'Smart extract'],
    '#securityMode option[value="none"]': ['암호 없음', 'None'],
    '#securityMode option[value="zip"]': ['내용만 암호화 (ZIP AES-256)', 'Encrypt contents (ZIP AES-256)'],
    '#securityMode option[value="private"]': ['파일명까지 암호화 (7Z)', 'Encrypt file names (7Z)'],
    '#passwordRandom': ['자동 생성', 'Random'],
    '#passwordPhrase': ['패스프레이즈', 'Phrase'],
    '#passwordCopy': ['복사', 'Copy'],
  };
  for (const [selector, values] of Object.entries(text)) {
    const node = document.querySelector(selector);
    if (node) node.textContent = packText(...values);
  }
  const showBtn = document.getElementById('passwordShow');
  const pwdEl = document.getElementById('txtCompressPwd');
  if (showBtn && pwdEl) {
    const visible = pwdEl.type === 'text';
    showBtn.textContent = visible ? packText('숨기기', 'Hide') : packText('표시', 'Show');
  }
  const pwdConfirm = document.getElementById('passwordConfirm');
  if (pwdConfirm) pwdConfirm.placeholder = packText('비밀번호 확인', 'Confirm password');

  const updateDesc = document.getElementById('packUpdateDescription');
  if (updateDesc) {
    updateDesc.textContent = isPackagedDistribution
      ? packText('이 설치본의 업데이트는 Microsoft Store에서 관리합니다.', 'Microsoft Store manages updates for this installation.')
      : packText('실행할 때 새 GitHub 릴리스를 자동으로 확인합니다.', 'Automatically checks GitHub for new releases on launch.');
  }
  if (isPackagedDistribution) document.getElementById('btnToolUpdate').textContent = packText('Store 열기', 'Open Store');
  renderWindowsAssociations();

  const labels = {
    packFormat: ['출력 형식', 'Output format'],
    packPassword: ['원본 비밀번호', 'Source password'],
    packOutputPassword: ['새 비밀번호', 'New password'],
    packToolPasswordConfirm: ['비밀번호 확인', 'Confirm password'],
    packMode: ['해제 방식', 'Extraction mode'],
    packSplitSize: ['분할 크기', 'Volume size'],
    securityMode: ['암호화 방식', 'Encryption'],
  };
  for (const [id, values] of Object.entries(labels)) {
    const label = document.getElementById(id)?.parentElement;
    if (label?.firstChild?.nodeType === Node.TEXT_NODE) {
      label.firstChild.textContent = packText(...values);
    }
  }
  const renumberSpan = document.getElementById('packRenumberLabel');
  if (renumberSpan) renumberSpan.textContent = packText('페이지 번호로 이름 정리', 'Number pages naturally');

  const names = {
    convert: ['포맷 변환', 'Convert'],
    batch: ['일괄 해제', 'Batch extract'],
    cbz: ['CBZ 만들기', 'Create CBZ'],
    privacy: ['파일명까지 암호화', 'Encrypt file names'],
    split: ['분할 압축', 'Split archive'],
  };
  document.querySelectorAll('.pack-tool-tab').forEach((button) => {
    button.lastElementChild.textContent = packText(...names[button.dataset.action]);
  });
  for (const id of ['packToolsButton', 'packSettingsButton']) {
    const button = document.getElementById(id);
    if (button && TRANSLATIONS[AppState.language][id]) {
      const label = TRANSLATIONS[AppState.language][id];
      button.setAttribute('aria-label', label);
      button.dataset.tooltip = label;
      button.removeAttribute('title');
    }
  }
  const infoBtn = document.getElementById('btnToolInfo');
  if (infoBtn) {
    const tip = isEn
      ? 'Help, official links, language, and display theme'
      : '정보, 공식 링크, 언어 및 화면 테마 설정';
    infoBtn.dataset.tooltip = tip;
    infoBtn.setAttribute('aria-label', tip);
    infoBtn.removeAttribute('title');
  }
  refreshPackPaths();
  if (document.getElementById('packAction')) updateToolFields();
  if (window.updateCompressSecurityUi) window.updateCompressSecurityUi();
  if (lastUpdateResult) handleUpdateCheck(lastUpdateResult, false);
};

function packModal(id, title, content) {
  const node = document.createElement('div');
  node.id = id;
  node.className = 'layer-modal-backdrop';
  node.innerHTML = `<div class="compact-modal pack-modal"><div class="modal-header"><span class="modal-title">${title}</span><button class="modal-close-btn" aria-label="닫기">&times;</button></div><div class="modal-body">${content}</div></div>`;
  node.querySelector('.modal-close-btn').onclick = () => node.classList.remove('active');
  document.body.append(node);
  return node;
}

function openPackTools(paths = [], action = 'convert') {
  toolPaths = Array.from(new Set(paths || []));
  document.getElementById('packAction').value = action;
  document.getElementById('packResult').textContent = '';
  refreshPackPaths();
  document.getElementById('packTools').classList.add('active');
  updateToolFields();
}
window.openPackTools = openPackTools;

function updateToolFields() {
  const action = document.getElementById('packAction').value;
  document.querySelectorAll('.pack-tool-tab').forEach((button) => {
    button.classList.toggle('active', button.dataset.action === action);
    button.setAttribute('aria-selected', String(button.dataset.action === action));
  });
  const descriptions = {
    convert: ['포맷 변환', '압축 파일을 ZIP, 7Z 또는 TAR 계열 형식으로 안전하게 변환합니다.'],
    batch: ['일괄 해제', '여러 압축 파일을 선택한 위치에 한 번에 풀어냅니다.'],
    cbz: ['CBZ 만들기', '이미지를 자연스러운 순서로 정리해 만화책용 CBZ를 만듭니다.'],
    privacy: ['파일명까지 암호화', '비밀번호 없이는 내용뿐 아니라 내부 파일명·폴더 목록도 볼 수 없는 7Z를 만듭니다.'],
    split: ['분할 압축', '큰 압축 파일을 선택한 크기의 번호 파일로 나눕니다.'],
  };
  const english = {
    convert: ['Convert', 'Convert an archive to ZIP, 7Z, or a TAR format.'],
    batch: ['Batch extract', 'Extract several archives into the selected location.'],
    cbz: ['Create CBZ', 'Arrange images in natural order and create a comic book archive.'],
    privacy: ['Encrypt file names', 'Require a password to view internal file names, folders, and contents.'],
    split: ['Split archive', 'Divide a large archive into numbered files of the selected size.'],
  };
  const [title, copy] = (AppState.language === 'en' ? english : descriptions)[action] || descriptions.convert;
  document.getElementById('packToolTitle').textContent = title;
  document.getElementById('packToolDescription').textContent = copy;
  document.querySelectorAll('[data-actions]').forEach((el) => {
    el.hidden = !el.dataset.actions.split(' ').includes(action);
  });
  document.querySelectorAll('#packFormat option').forEach((option) => {
    option.disabled = action === 'split' && !['ZIP', '7Z'].includes(option.value);
  });
  if (action === 'split' && !['ZIP', '7Z'].includes(document.getElementById('packFormat').value)) {
    document.getElementById('packFormat').value = 'ZIP';
  }
}

function handleUpdateCheck(result, manual = false) {
  lastUpdateResult = result;
  const status = document.getElementById('packUpdateStatus');
  if (!result.success) {
    const reasons = {
      rate_limit: packText('GitHub 요청이 제한되어 버전을 확인하지 못했습니다. 잠시 후 다시 시도하세요.', 'GitHub limited the request. Try again later.'),
      http_error: packText('GitHub 서버 응답 오류로 버전을 확인하지 못했습니다.', 'A GitHub server error prevented the version check.'),
      tls_error: packText('보안 연결을 확인하지 못했습니다. Windows 날짜·시간과 인증서를 확인하세요.', 'Could not verify the secure connection. Check the Windows clock and certificates.'),
      invalid_response: packText('업데이트 응답이 올바르지 않아 최신 여부를 확인하지 못했습니다.', 'The update response was invalid; the latest version could not be determined.'),
      network_error: packText('최신 버전을 확인하지 못했습니다. 인터넷 연결 후 다시 시도하세요.', 'Could not check for updates. Check your connection and try again.')
    };
    if (status) { status.textContent = reasons[result.error_code] || reasons.network_error; status.title = result.error || ''; }
    if (manual) alert(`${packText('업데이트 확인 실패', 'Update check failed')}\n${result.error}`);
    return;
  }
  if (status) status.title = '';
  if (!result.update_available) {
    if (status) status.textContent = packText('현재 최신 버전입니다.', 'CrowPack is up to date.');
    if (manual) alert(`CrowPack v${result.version}\n${packText('현재 최신 버전을 사용하고 있습니다.', 'You are using the latest version.')}`);
    return;
  }
  if (status) status.textContent = `${result.latest_tag} ${packText('사용 가능', 'available')}`;
  const size = result.asset_size ? ` (${formatBytes(result.asset_size)})` : '';
  if (result.store_managed) {
    const approved = confirm(
      `${packText('새 CrowPack 버전을 사용할 수 있습니다.', 'A new CrowPack version is available.')}\n\n` +
      `${result.version} → ${result.latest_tag}\n` +
      `${packText('Microsoft Store 업데이트 페이지를 여시겠습니까?', 'Open the Microsoft Store update page?')}`
    );
    if (!approved) {
      if (status) status.textContent = packText('업데이트를 나중에 진행합니다.', 'Update postponed.');
      return;
    }
    AppState.pyBridge.openStoreUpdate((raw) => {
      const opened = JSON.parse(raw);
      if (status) {
        status.textContent = opened.success
          ? packText('Microsoft Store를 열었습니다.', 'Microsoft Store opened.')
          : packText('Microsoft Store를 열 수 없습니다.', 'Could not open Microsoft Store.');
      }
      if (!opened.success && manual) alert(opened.error);
    });
    return;
  }
  const approved = confirm(
    `${packText('새 CrowPack 버전을 사용할 수 있습니다.', 'A new CrowPack version is available.')}\n\n` +
    `${result.version} → ${result.latest_tag}${size}\n` +
    `${packText('GitHub에서 설치 파일을 다운로드하고 SHA-256을 확인한 뒤 업데이트하시겠습니까?', 'Download the installer from GitHub, verify its SHA-256, and update now?')}`
  );
  if (!approved) {
    if (status) status.textContent = packText('업데이트를 나중에 진행합니다.', 'Update postponed.');
    return;
  }
  if (status) status.textContent = packText('업데이트 다운로드 준비 중…', 'Preparing update download…');
  AppState.pyBridge.downloadAndInstallUpdate(result.latest_tag);
}

function requestUpdateCheck(manual = false) {
  if (!AppState.pyBridge || isPackagedDistribution === null) return;
  if (isPackagedDistribution) {
    if (manual) AppState.pyBridge.openStoreUpdate(raw => {
      const result = JSON.parse(raw);
      if (!result.success) alert(packText('Microsoft Store를 열 수 없습니다.', 'Could not open Microsoft Store.'));
    });
    return;
  }
  manualUpdateCheck = manualUpdateCheck || manual;
  document.getElementById('packUpdateStatus').title = '';
  document.getElementById('packUpdateStatus').textContent = packText('최신 버전을 확인하는 중입니다…', 'Checking for updates…');
  AppState.pyBridge.checkForUpdatesAsync();
}

window.validateSecurity = () => {
  const security = document.getElementById('securityMode').value;
  const pwd = document.getElementById('txtCompressPwd').value;
  if (security !== 'none' && (!pwd || pwd !== document.getElementById('passwordConfirm').value)) {
    alert(packText('비밀번호와 확인 값이 일치해야 합니다.', 'Enter matching passwords.'));
    return false;
  }
  if (security !== 'none') document.getElementById('selCompressFmt').value = security === 'private' ? '7Z' : 'ZIP';
  if (security === 'none') document.getElementById('txtCompressPwd').value = '';
  return true;
};

const originalOpenArchive = openArchiveFile;
openArchiveFile = function(path) {
  if (!AppState.pyBridge) return;
  AppState.archivePassword = '';
  AppState.pyBridge.listArchive(path, '', AppState.selectedEncoding === 'auto' ? '' : AppState.selectedEncoding, (raw) => {
    const info = JSON.parse(raw);
    if (!info.error) {
      if (info.items.some((item) => item.is_encrypted)) {
        AppState.pyBridge.requestPassword(packText('암호화된 파일의 비밀번호', 'Encrypted archive password'), (pwd) => {
          AppState.archivePassword = pwd;
          showExplorerView(info);
        });
      } else {
        showExplorerView(info);
      }
      return;
    }
    AppState.pyBridge.requestPassword(packText('암호가 있는 파일이면 비밀번호를 입력하세요.', 'Enter the archive password, if encrypted.'), (pwd) => {
      if (!pwd) { alert(info.error); return; }
      AppState.pyBridge.listArchive(path, pwd, '', (result) => {
        const retry = JSON.parse(result);
        if (retry.error) { alert(retry.error); return; }
        AppState.archivePassword = pwd;
        showExplorerView(retry);
      });
    });
  });
};

const previousDrop = handleDroppedFiles;
handleDroppedFiles = function(paths) {
  if (!AppState.pyBridge) { window.pendingNativeDrop = paths; return; }
  const packToolsEl = document.getElementById('packTools');
  if (packToolsEl && packToolsEl.classList.contains('active')) {
    addPathsToPackTools(paths);
    return;
  }
  if (paths.length > 1 && paths.every((p) => /\.(zip|7z|rar|alz|egg|tar|gz|bz2|xz|cab|iso|cbz)$/i.test(p))) {
    openPackTools(paths, 'batch');
    return;
  }
  if (paths.length === 1 && /\.cbz$/i.test(paths[0])) {
    openArchiveFile(paths[0]);
    return;
  }
  previousDrop(paths);
};
window.handleNativeDrop = window.handleDroppedFiles = handleDroppedFiles;

document.addEventListener('DOMContentLoaded', () => {
  const tools = packModal('packTools', '도구', `
    <input type="hidden" id="packAction" value="convert">
    <div class="pack-tool-tabs" role="tablist" aria-label="도구 선택">
      ${[['convert', 'convert', '포맷 변환'], ['batch', 'batch', '일괄 해제'], ['cbz', 'cbz', 'CBZ 만들기'], ['privacy', 'privacy', '파일명까지 암호화'], ['split', 'split', '분할 압축']].map(([action, icon, label]) => `<button class="pack-tool-tab" data-action="${action}" role="tab"><span class="pack-tool-icon">${window.CrowIcons[icon]}</span><span>${label}</span></button>`).join('')}
    </div>
    <div class="pack-tool-intro"><strong id="packToolTitle"></strong><span id="packToolDescription"></span></div>
    <div class="pack-row"><button class="btn" id="packSelect">파일 선택</button><button class="btn" id="packFolder">폴더 추가</button><button class="btn" id="packClear">비우기</button></div>
    <pre id="packPaths" class="pack-result is-empty"></pre>
    <div class="pack-options-grid">
      <label data-actions="convert split">출력 형식<select class="form-control" id="packFormat">${['ZIP', '7Z', 'TAR', 'TAR.GZ', 'TAR.BZ2', 'TAR.XZ'].map((x) => `<option>${x}</option>`).join('')}</select></label>
      <label data-actions="convert batch">원본 비밀번호<input type="password" id="packPassword" class="form-control" autocomplete="off"></label>
      <label data-actions="convert privacy">새 비밀번호<input type="password" id="packOutputPassword" class="form-control" autocomplete="off"></label>
      <label data-actions="privacy">비밀번호 확인<input type="password" id="packToolPasswordConfirm" class="form-control" autocomplete="off"></label>
      <label data-actions="batch">해제 방식<select id="packMode" class="form-control"><option value="new_folder">각각 별도 폴더</option><option value="current">현재 폴더</option><option value="smart">알아서 풀기</option></select></label>
      <label data-actions="split">분할 크기<select id="packSplitSize" class="form-control"><option value="10">10 MB</option><option value="50">50 MB</option><option value="100" selected>100 MB</option><option value="500">500 MB</option><option value="1024">1 GB</option></select></label>
      <label data-actions="cbz" class="pack-check"><input type="checkbox" id="packRenumber" checked><span id="packRenumberLabel">페이지 번호로 이름 정리</span></label>
    </div>
    <button id="packRun" class="btn primary">실행</button>
    <pre id="packResult" class="pack-result" role="status"></pre><button id="packCopy" class="btn">결과 복사</button>`);

  const settings = packModal('packSettings', '설정', `
    <section class="settings-section"><h3 id="packSectionDisplayTitle">화면</h3><div id="packGeneral"></div></section>
    <section class="settings-section"><h3 id="packSectionWindowsTitle">Windows 연결</h3>
      <div class="settings-action-row"><div><strong id="packAssocTitle">압축 파일 기본 앱</strong><span id="packAssociations">현재 연결 상태 확인 중</span></div><button class="btn" id="packDefaults">Windows 설정</button></div>
      <div class="settings-action-row" id="packShellIntegration"><div><strong id="packShellTitle">탐색기 우클릭 메뉴</strong><span id="packShellDesc">압축 및 해제 명령을 표시합니다.</span></div><div class="pack-row"><button class="btn" id="packShellOn">사용</button><button class="btn" id="packShellOff">해제</button></div></div>
    </section>
    <section class="settings-section"><h3 id="packSectionUpdateTitle">업데이트</h3>
      <div class="settings-action-row"><div><strong>CrowPack v1.7</strong><span id="packUpdateDescription">실행할 때 새 GitHub 릴리스를 자동으로 확인합니다.</span><span id="packUpdateStatus" role="status"></span></div><div id="packUpdateButton"></div></div>
    </section>`);

  document.body.insertAdjacentHTML('beforeend', `
    <dialog id="packWindowsSetup" aria-labelledby="packWindowsSetupTitle">
      <div class="compact-modal pack-modal">
        <header class="modal-header"><h2 class="modal-title" id="packWindowsSetupTitle">CrowPack Windows 설정</h2></header>
        <div class="modal-body">
          <p id="packWindowsSetupIntro"></p>
          <ul id="packAssociationList"></ul>
          <button type="button" class="btn" id="packOpenDefaultApps">기본 앱 설정 열기</button>
          <button type="button" class="btn" id="packCreateShortcut" hidden>바탕화면 바로가기 만들기</button>
          <p id="packWindowsSetupStatus" role="status" hidden></p>
        </div>
        <footer class="modal-footer"><button type="button" class="btn" id="packFinishWindowsSetup" autofocus>닫기</button></footer>
      </div>
    </dialog>`);

  document.getElementById('packGeneral').append(document.querySelector('#modalInfoApp .settings-panel'));
  document.getElementById('packUpdateButton').append(document.getElementById('btnToolUpdate'));
  document.querySelector('#packGeneral .settings-title').textContent = '언어와 테마';
  const updateButton = document.getElementById('btnToolUpdate');
  updateButton.className = 'btn';
  updateButton.innerHTML = '업데이트 확인';
  document.getElementById('btnToolAssociations').remove();

  const nav = document.getElementById('navGroupHome');
  for (const [id, label, icon, modal] of [['packToolsButton', '도구', 'tools', tools], ['packSettingsButton', '설정', 'settings', settings]]) {
    const b = document.createElement('button');
    b.id = id;
    b.className = 'tool-icon-btn labeled-tool-btn';
    b.innerHTML = `<span>${window.CrowIcons[icon] || ''}</span><span class="tool-btn-label">${label}</span>`;
    b.onclick = () => {
      modal.classList.add('active');
      if (modal === settings) refreshWindowsAssociations();
    };
    nav.insertBefore(b, document.getElementById('btnToolInfo'));
    b.querySelector('.tool-btn-label').dataset.i18n = id;
    b.dataset.tooltip = label;
    b.setAttribute('aria-label', label);
  }

  TRANSLATIONS.ko.packToolsButton = '도구';
  TRANSLATIONS.en.packToolsButton = 'Tools';
  TRANSLATIONS.ko.packSettingsButton = '설정';
  TRANSLATIONS.en.packSettingsButton = 'Settings';
  TRANSLATIONS.ko['nav.info'] = '도움말';
  TRANSLATIONS.en['nav.info'] = 'Help';
  TRANSLATIONS.ko['info.title'] = '도움말';
  TRANSLATIONS.en['info.title'] = 'Help';
  TRANSLATIONS.ko['info.help'] += '<br>• <strong>파일명 암호화</strong>: 7Z 파일 내용·이름 암호화. 비밀번호는 다른 수단으로 전달하세요.<br>• <strong>드래그 복사</strong>: 목록에서 파일을 잡아 Explorer 폴더로 끌면 선택 항목을 복사합니다.<br>• <strong>CBZ</strong>: 순서 있는 이미지 문서용 ZIP. ZIP/7Z/RAR/TAR/ALZ/EGG/CAB/ISO 지원.';
  TRANSLATIONS.en['info.help'] += '<br>• <strong>Encrypt file names</strong>: encrypted 7Z contents and names. Share the password separately.<br>• <strong>Drag export</strong>: Drag selected archive items into Explorer to copy them.<br>• <strong>CBZ</strong>: Ordered comic ZIP. Supports ZIP/7Z/RAR/TAR/ALZ/EGG/CAB/ISO.';

  const pwd = document.getElementById('txtCompressPwd');
  pwd.insertAdjacentHTML('beforebegin', `<label>암호화 방식<select id="securityMode" class="form-control"><option value="none">암호 없음</option><option value="zip">내용만 암호화 (ZIP AES-256)</option><option value="private">파일명까지 암호화 (7Z)</option></select></label><p id="securityNote" class="preset-note"></p>`);
  pwd.insertAdjacentHTML('afterend', `<input type="password" id="passwordConfirm" class="form-control" placeholder="비밀번호 확인" autocomplete="off"><div class="pwd-tools-row"><button type="button" class="btn" id="passwordShow">표시</button><button type="button" class="btn" id="passwordRandom">자동 생성</button><button type="button" class="btn" id="passwordPhrase">패스프레이즈</button><button type="button" class="btn" id="passwordCopy">복사</button></div><span id="passwordStrength" role="status"></span>`);

  const confirmation = document.getElementById('passwordConfirm');
  const strength = () => {
    const mode = document.getElementById('securityMode').value;
    const strengthEl = document.getElementById('passwordStrength');
    if (mode === 'none') {
      strengthEl.textContent = packText('암호 보호 사용 안 함', 'Password protection off');
      return;
    }
    const length = pwd.value.length;
    const level = packText(
      length >= 20 ? '강함' : length >= 12 ? '보통' : '짧음',
      length >= 20 ? 'Strong' : length >= 12 ? 'Moderate' : 'Short'
    );
    const match = packText(
      pwd.value && pwd.value === confirmation.value ? '일치' : '불일치',
      pwd.value && pwd.value === confirmation.value ? 'Match' : 'Mismatch'
    );
    strengthEl.textContent = `${level} · ${match}`;
  };
  pwd.oninput = confirmation.oninput = strength;

  const security = () => {
    const mode = document.getElementById('securityMode').value;
    pwd.disabled = confirmation.disabled = mode === 'none';
    if (mode === 'none') {
      pwd.type = confirmation.type = 'password';
      document.getElementById('passwordShow').textContent = packText('표시', 'Show');
    } else {
      document.getElementById('selCompressFmt').value = mode === 'private' ? '7Z' : 'ZIP';
    }
    document.getElementById('securityNote').textContent = mode === 'private'
      ? packText('비밀번호 없이는 내부 파일명·폴더 목록과 내용을 볼 수 없습니다.', 'A password is required to see file names, folders, and contents.')
      : mode === 'zip'
        ? packText('내용은 암호화되지만 내부 파일명·폴더 목록은 보입니다.', 'Contents are encrypted; file names and folders remain visible.')
        : packText('비밀번호 없이 바로 열 수 있는 일반 압축 파일을 만듭니다.', 'Creates an unencrypted standard archive.');
    strength();
  };
  window.updateCompressSecurityUi = security;
  document.getElementById('securityMode').onchange = security;

  document.getElementById('passwordShow').onclick = () => {
    const nextType = pwd.type === 'password' ? 'text' : 'password';
    pwd.type = confirmation.type = nextType;
    document.getElementById('passwordShow').textContent = nextType === 'text'
      ? packText('숨기기', 'Hide')
      : packText('표시', 'Show');
  };
  for (const [id, mode] of [['passwordRandom', 'random'], ['passwordPhrase', 'phrase']]) {
    document.getElementById(id).onclick = () => {
      if (document.getElementById('securityMode').value === 'none') {
        document.getElementById('securityMode').value = 'zip';
        security();
      }
      AppState.pyBridge?.generatePassword(mode, (value) => {
        pwd.value = confirmation.value = value;
        strength();
      });
    };
  }
  document.getElementById('passwordCopy').onclick = () => {
    if (!pwd.value) return;
    AppState.pyBridge?.copyText(pwd.value);
    if (window.showCrowToast) window.showCrowToast(packText('비밀번호를 클립보드에 복사했습니다.', 'Password copied to clipboard.'));
  };

  document.querySelectorAll('.pack-tool-tab').forEach((button) => {
    button.onclick = () => {
      document.getElementById('packAction').value = button.dataset.action;
      document.getElementById('packResult').textContent = '';
      updateToolFields();
    };
  });
  updateToolFields();

  document.getElementById('packSelect').onclick = () => AppState.pyBridge?.selectSourceFiles((r) => addPathsToPackTools(JSON.parse(r)));
  document.getElementById('packFolder').onclick = () => AppState.pyBridge?.selectSourceFolder((r) => addPathsToPackTools(JSON.parse(r)));
  document.getElementById('packClear').onclick = () => { toolPaths = []; refreshPackPaths(); };
  document.getElementById('packCopy').onclick = () => {
    if (!lastToolText) return;
    AppState.pyBridge?.copyText(lastToolText);
    if (window.showCrowToast) window.showCrowToast(packText('작업 결과를 복사했습니다.', 'Result copied to clipboard.'));
  };
  const windowsSetup = document.getElementById('packWindowsSetup');
  const windowsStatus = document.getElementById('packWindowsSetupStatus');
  const shortcut = document.getElementById('packCreateShortcut');
  document.getElementById('packDefaults').onclick = openWindowsSetup;
  document.getElementById('packFinishWindowsSetup').onclick = () => windowsSetup.close();
  document.getElementById('packOpenDefaultApps').onclick = () => AppState.pyBridge?.openDefaultApps(raw => {
    const result = JSON.parse(raw);
    if (!result.success) alert(packText('기본 앱 설정을 열 수 없습니다.', 'Could not open default app settings.') + '\n' + result.error);
  });
  shortcut.onclick = () => {
    if (!AppState.pyBridge) return;
    shortcut.disabled = true;
    AppState.pyBridge.createDesktopShortcut(raw => {
      const result = JSON.parse(raw);
      const messages = {
        created: packText('바탕화면에 바로가기를 만들었습니다.', 'Desktop shortcut created.'),
        exists: packText('바탕화면에 바로가기가 이미 있습니다.', 'The desktop shortcut already exists.'),
        occupied: packText('바탕화면에 같은 이름의 다른 바로가기가 있습니다.', 'A different shortcut already uses that name.')
      };
      windowsStatus.textContent = messages[result.state || result.error_code]
        || packText('바로가기를 만들 수 없습니다.', 'Could not create the desktop shortcut.');
      windowsStatus.title = result.error || '';
      windowsStatus.hidden = false;
      shortcut.disabled = result.success;
    });
  };
  window.addEventListener('focus', () => {
    if (windowsSetup.open) refreshWindowsAssociations();
  });
  for (const [id, enabled] of [['packShellOn', true], ['packShellOff', false]]) {
    document.getElementById(id).onclick = () => AppState.pyBridge?.setShellIntegration(enabled, (r) => {
      const x = JSON.parse(r);
      if (x.success && window.showCrowToast) window.showCrowToast(packText('우클릭 메뉴 설정이 적용되었습니다.', 'Context menu updated.'));
      else alert(x.success ? packText('완료', 'Done') : x.error);
    });
  }
  updateButton.onclick = () => {
    document.getElementById('packUpdateStatus').textContent = packText('확인 중…', 'Checking…');
    requestUpdateCheck(true);
  };
  document.getElementById('packRun').onclick = () => {
    if (!toolPaths.length || !AppState.pyBridge) return;
    const action = document.getElementById('packAction').value;
    const value = (id) => document.getElementById(id).value;
    if (action === 'convert' && toolPaths.length !== 1) {
      alert(packText('변환할 파일 한 개를 선택하세요.', 'Select one file to convert.'));
      return;
    }
    if (action === 'privacy' && (!value('packOutputPassword') || value('packOutputPassword') !== value('packToolPasswordConfirm'))) {
      alert(packText('비밀번호와 확인 값이 일치해야 합니다.', 'Enter matching passwords.'));
      return;
    }
    document.getElementById('packRun').disabled = true;
    document.getElementById('packResult').textContent = packText('처리 중…', 'Working…');
    AppState.pyBridge.runTool(JSON.stringify({
      action,
      paths: toolPaths,
      format: value('packFormat'),
      password: value('packPassword'),
      outputPassword: value('packOutputPassword'),
      mode: value('packMode'),
      splitSize: value('packSplitSize'),
      renumber: document.getElementById('packRenumber').checked
    }));
    document.getElementById('packPassword').value = document.getElementById('packOutputPassword').value = document.getElementById('packToolPasswordConfirm').value = '';
  };

  applyLanguage(AppState.language);

  const timer = setInterval(() => {
    if (!AppState.pyBridge) return;
    clearInterval(timer);
    AppState.pyBridge.toolFinished.connect((raw) => {
      const result = JSON.parse(raw);
      document.getElementById('packRun').disabled = false;
      if (!result.success) {
        lastToolText = result.cancelled ? packText('취소됨', 'Cancelled') : result.error;
      } else if (result.action === 'batch') {
        const ok = result.result.filter((x) => x.success).length;
        lastToolText = `${packText('성공', 'Success')}: ${ok} · ${packText('실패', 'Failed')}: ${result.result.length - ok}\n` +
          result.result.map((x) => `${x.success ? '✓' : '✕'} ${x.path}\n${x.error || x.output_dir}`).join('\n');
      } else {
        lastToolText = String(result.result);
      }
      document.getElementById('packResult').textContent = lastToolText;
    });
    AppState.pyBridge.progressEvent.connect((cur, total, name) => {
      if (document.getElementById('packRun').disabled) {
        document.getElementById('packResult').textContent = `${cur} / ${total}\n${name}`;
      }
    });
    AppState.pyBridge.updateCheckFinished.connect((raw) => {
      const manual = manualUpdateCheck;
      manualUpdateCheck = false;
      handleUpdateCheck(JSON.parse(raw), manual);
    });
    AppState.pyBridge.updateProgress.connect((cur, total) => {
      const percent = Math.min(100, Math.round(cur * 100 / Math.max(1, total)));
      document.getElementById('packUpdateStatus').textContent = `${packText('다운로드 중', 'Downloading')} ${percent}%`;
    });
    AppState.pyBridge.updateFinished.connect((raw) => {
      const result = JSON.parse(raw);
      if (!result.success) {
        document.getElementById('packUpdateStatus').textContent = packText('업데이트 실패', 'Update failed');
        alert(`${packText('업데이트 실패', 'Update failed')}\n${result.error}`);
        return;
      }
      document.getElementById('packUpdateStatus').textContent = packText('설치 프로그램 시작됨', 'Installer started');
      alert(result.message);
      setTimeout(() => AppState.pyBridge.quitForUpdate(), 250);
    });
    AppState.pyBridge.getDistributionInfo(raw => {
      const distribution = JSON.parse(raw);
      isPackagedDistribution = Boolean(distribution.packaged);
      document.getElementById('packShellIntegration').hidden = isPackagedDistribution;
      shortcut.hidden = !distribution.desktop_setup;
      applyPackLanguage();
      if (distribution.offer_windows_setup) {
        openWindowsSetup();
        AppState.pyBridge.markWindowsSetupSeen();
        windowsSetup.addEventListener('close', () => requestUpdateCheck(false), {once: true});
      } else {
        requestUpdateCheck(false);
      }
    });
    if (window.pendingShellAction) window.handleShellAction(...window.pendingShellAction);
    if (window.pendingNativeDrop) {
      const paths = window.pendingNativeDrop;
      window.pendingNativeDrop = null;
      handleDroppedFiles(paths);
    }
  }, 100);
});

window.handleShellAction = (action, paths) => {
  if (!AppState.pyBridge || !document.getElementById('packTools')) {
    window.pendingShellAction = [action, paths];
    return;
  }
  window.pendingShellAction = null;
  if (['zip', '7z', 'private', 'compress'].includes(action)) {
    addPathsToCompress(paths);
    openNewCompressModal();
    document.getElementById('selCompressFmt').value = action === '7z' || action === 'private' ? '7Z' : 'ZIP';
    document.getElementById('securityMode').value = action === 'private' ? 'private' : 'none';
    document.getElementById('securityMode').dispatchEvent(new Event('change'));
  } else if (action === 'open') {
    openArchiveFile(paths[0]);
  } else if (action === 'test') {
    AppState.pyBridge.testArchive(paths[0], '', (r) => alert(r));
  } else {
    openPackTools(paths, action.startsWith('convert') ? 'convert' : 'batch');
    if (action === 'convert7z') document.getElementById('packFormat').value = '7Z';
    if (action === 'here') document.getElementById('packMode').value = 'current';
    if (action === 'smart') document.getElementById('packMode').value = 'smart';
  }
};

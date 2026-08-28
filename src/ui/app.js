/**
 * Crow Pack v1.0d - Frontend Interaction Logic
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
  selectedItems: new Set(),
  compressSourcePaths: [],
  selectedEncoding: 'auto',
  lastExtractedFolder: null,
  contextEntry: null,
  pyBridge: null
};

const IMAGE_PREVIEW_PATTERN = /\.(bmp|gif|jpe?g|png|webp)$/i;

function setNativeDragActive(active) {
  const dropZone = document.getElementById('homeDropZone');
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
  showProgress('그림 미리보기 준비 중...', entry.name);
  AppState.pyBridge.getImagePreview(
    AppState.currentArchiveInfo.file_path,
    entry.fullName,
    '',
    (resJson) => {
      hideProgress();
      const result = JSON.parse(resJson);
      if (!result.success) {
        alert('그림 미리보기 실패: ' + result.error);
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
  showProgress(moveAfterCopy ? '파일 이동 중...' : '파일 복사 중...', items[0]);
  AppState.pyBridge.exportArchiveItems(
    AppState.currentArchiveInfo.file_path,
    JSON.stringify(items),
    moveAfterCopy,
    (resJson) => {
      const result = JSON.parse(resJson);
      if (!result.success) {
        hideProgress();
        if (!result.cancelled) alert((moveAfterCopy ? '파일 이동 실패: ' : '파일 복사 실패: ') + result.error);
        return;
      }
      if (moveAfterCopy) {
        hideProgress();
        openArchiveFile(AppState.currentArchiveInfo.file_path);
      } else {
        finishProgress(`${result.copied_count}개 파일 복사 완료`, result.dest_dir);
      }
    }
  );
}

function deleteContextItems() {
  hideArchiveContextMenu();
  if (!AppState.currentArchiveInfo || !AppState.pyBridge) return;
  const items = getContextItems();
  if (items.length === 0 || !confirm(`선택한 ${items.length}개 항목을 ZIP에서 삭제하시겠습니까?`)) return;
  showProgress('파일 삭제 중...', items[0]);
  AppState.pyBridge.deleteFilesFromArchive(
    AppState.currentArchiveInfo.file_path,
    JSON.stringify(items),
    (resJson) => {
      hideProgress();
      const result = JSON.parse(resJson);
      if (result.success) openArchiveFile(AppState.currentArchiveInfo.file_path);
      else alert('파일 삭제 실패: ' + result.error);
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
  setHtml('iconToolOpenIso', I.isoDisc);
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
}

// --------------------------------------------------------------------------
// 2. 전역 플로팅 툴팁 엔진 (마우스 오버 시 메뉴 설명 100% 노출)
// --------------------------------------------------------------------------
function initFloatingTooltips() {
  const tooltipEl = document.getElementById('floatingCrowTooltip');
  if (!tooltipEl) return;

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
function showHomeView() {
  AppState.currentView = 'home';
  AppState.currentArchiveInfo = null;
  AppState.currentDirectory = '';
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
  AppState.selectedItems.clear();

  document.getElementById('viewHome').classList.remove('active');
  document.getElementById('viewExplorer').classList.add('active');

  // 아카이브 열림: 아카이브 조작 툴바 노출, 홈 툴바 숨김
  document.getElementById('navGroupExplorer').style.display = 'flex';
  document.getElementById('navGroupHome').style.display = 'none';

  const isReadOnly = Boolean(archiveInfo.is_read_only);
  document.getElementById('btnToolAdd').style.display = isReadOnly ? 'none' : '';
  document.getElementById('btnToolDelete').style.display = isReadOnly ? 'none' : '';
  document.getElementById('btnToolCodePage').style.display = isReadOnly ? 'none' : '';
  const hereButton = document.getElementById('btnToolExtractHere');
  const customButton = document.getElementById('btnToolExtractCustom');
  const hereLabel = isReadOnly ? 'ISO 파일을 현재 폴더로 복사' : '현재 폴더에 풀기 (스마트 알아서 풀기)';
  const customLabel = isReadOnly ? 'ISO 파일을 지정 폴더로 복사' : '폴더 지정하여 풀기';
  hereButton.title = hereLabel;
  hereButton.dataset.tooltip = hereLabel;
  customButton.title = customLabel;
  customButton.dataset.tooltip = customLabel;

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
        <span class="file-icon-svg folder">${window.CrowIcons.folderUp}</span>
        <strong>[.. 상위 폴더]</strong>
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

  const sortedItems = Array.from(currentLevelItems.values()).sort((a, b) => {
    if (a.isDir && !b.isDir) return -1;
    if (!a.isDir && b.isDir) return 1;
    return a.name.localeCompare(b.name);
  });

  sortedItems.forEach(entry => {
    const tr = document.createElement('tr');
    tr.dataset.fullName = entry.fullName;

    const isChecked = AppState.selectedItems.has(entry.fullName);
    const iconSvg = entry.isDir ? window.CrowIcons.folder : window.CrowIcons.file;
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
    chk.addEventListener('change', (e) => {
      e.stopPropagation();
      if (chk.checked) AppState.selectedItems.add(entry.fullName);
      else AppState.selectedItems.delete(entry.fullName);
      updateExplorerStatusBar();
    });

    chk.addEventListener('click', (e) => {
      e.stopPropagation();
    });

    checkboxCell.addEventListener('click', (e) => {
      e.stopPropagation();
      if (e.target !== chk) {
        chk.checked = !chk.checked;
        chk.dispatchEvent(new Event('change'));
      }
    });

    tr.addEventListener('click', () => {
      chk.checked = !chk.checked;
      chk.dispatchEvent(new Event('change'));
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
      showArchiveContextMenu(e, entry);
    });

    tbody.appendChild(tr);
  });

  updateExplorerStatusBar();
}

function updateExplorerStatusBar() {
  const info = AppState.currentArchiveInfo;
  if (!info) return;

  const totalFiles = info.file_count;
  const selCount = AppState.selectedItems.size;
  const summaryEl = document.getElementById('statExplorerSummary');
  const sizesEl = document.getElementById('statExplorerSizes');

  if (selCount > 0) {
    summaryEl.textContent = `${selCount}개 선택됨 (전체 ${totalFiles}개 파일)`;
  } else {
    summaryEl.textContent = `총 ${totalFiles}개 파일 (${info.dir_count}개 폴더)`;
  }

  sizesEl.textContent = `원본 ${formatBytes(info.uncompressed_size)} / 압축 ${formatBytes(info.compressed_size || info.archive_size)} (절감률 ${info.compression_ratio}%)`;
}

// 파일 임시 추출 및 실행
function openFileTemp(itemName) {
  if (!AppState.currentArchiveInfo || !AppState.pyBridge) return;
  showProgress('파일 여는 중...', itemName);
  AppState.pyBridge.extractSingleAndOpen(AppState.currentArchiveInfo.file_path, itemName, "", (resJson) => {
    hideProgress();
    const res = JSON.parse(resJson);
    if (!res.success) {
      alert('파일을 열 수 없습니다: ' + res.error);
    }
  });
}

// --------------------------------------------------------------------------
// 5. 드래그 앤 드롭 파일 처리 (새로 압축 리스트 즉시 반영 보장)
// --------------------------------------------------------------------------
function handleDroppedFiles(filePaths) {
  if (!filePaths || filePaths.length === 0) return;

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
  showProgress('아카이브 분석 중...', filePath.split(/[\\/]/).pop());
  
  const enc = AppState.selectedEncoding === 'auto' ? '' : AppState.selectedEncoding;
  AppState.pyBridge.listArchive(filePath, "", enc, (resJson) => {
    hideProgress();
    const info = JSON.parse(resJson);
    if (info.error) {
      alert('압축 파일을 열 수 없습니다: ' + info.error);
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
    container.innerHTML = '<div style="padding: 10px; text-align: center; color: var(--text-muted);">압축할 파일이나 폴더를 추가하거나 이곳으로 끌어다 놓으세요.</div>';
    return;
  }

  // 1단계: 즉시 동기 렌더링
  container.innerHTML = '';
  const totalInfo = document.createElement('div');
  totalInfo.style.cssText = 'font-weight: 700; color: #c7d2fe; margin-bottom: 6px;';
  totalInfo.id = 'lblCompressTotalInfo';
  totalInfo.textContent = `총 ${paths.length}개 항목 등록됨 (상세 분석 중...)`;
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
          lbl.textContent = `총 ${details.file_count}개 파일 (${formatBytes(details.total_size)})`;
        }
      }
    });
  }
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

function showProgress(title, currentFile = "준비 중...") {
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
  document.getElementById('progressPercentLbl').textContent = '100% 완료';
  document.getElementById('progressTitleText').textContent = '작업 완료!';
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
      console.log('PySide6 Native Bridge Connected (Crow Pack v1.0d)!');

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

  document.getElementById('btnToolOpenIso').onclick = () => {
    if (AppState.pyBridge) {
      AppState.pyBridge.selectIsoFile((filePath) => {
        if (filePath) openArchiveFile(filePath);
      });
    }
  };

  document.getElementById('btnToolPdfOptimize').onclick = () => {
    if (!AppState.pyBridge) return;
    showProgress('PDF 무손실 최적화 중...', 'PDF를 선택하세요.');
    AppState.pyBridge.optimizePdf((resJson) => {
      const result = JSON.parse(resJson);
      if (!result.success) {
        hideProgress();
        if (!result.cancelled) alert('PDF 최적화 실패: ' + result.error);
        return;
      }
      if (!result.output_path) {
        hideProgress();
        alert(result.message);
        return;
      }
      finishProgress(
        `${result.message} ${formatBytes(result.saved_bytes)} 절감`,
        result.output_dir
      );
    });
  };

  document.getElementById('btnToolUpdate').onclick = () => {
    if (!AppState.pyBridge) return;
    AppState.pyBridge.checkForUpdates((resJson) => {
      const result = JSON.parse(resJson);
      alert(`Crow Pack v${result.version}\n${result.message}`);
    });
  };

  document.getElementById('btnToolAssociations').onclick = () => {
    if (!AppState.pyBridge) return;
    AppState.pyBridge.registerFileAssociations((resJson) => {
      const result = JSON.parse(resJson);
      if (result.success) alert(result.message);
      else alert('확장자 연결 등록 실패: ' + result.error);
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
      isReadOnly ? 'ISO 파일 복사 중...' : '스마트 압축 풀기 중...',
      useDefaultDir ? '현재 폴더로 처리 중...' : '지정된 폴더로 처리 중...'
    );

    if (AppState.pyBridge) {
      AppState.pyBridge.extractArchiveWithOption(archivePath, "smart", useDefaultDir, selJson, "", (resJson) => {
        const res = JSON.parse(resJson);
        if (res.success) {
          finishProgress(`${res.extracted_count}개 파일 ${isReadOnly ? '복사' : '해제'} 완료`, res.dest_dir);
        } else {
          hideProgress();
          if (res.error && !res.error.includes("취소")) {
            alert((isReadOnly ? 'ISO 파일 복사 실패: ' : '압축 해제 실패: ') + res.error);
          }
        }
      });
    }
  }

  // [테스트]
  document.getElementById('btnToolTest').onclick = () => {
    if (!AppState.currentArchiveInfo || !AppState.pyBridge) return;
    showProgress('무결성 검사 중...', '손상 여부를 테스트하고 있습니다.');
    AppState.pyBridge.testArchive(AppState.currentArchiveInfo.file_path, "", (resJson) => {
      hideProgress();
      const res = JSON.parse(resJson);
      if (res.success) {
        alert('✅ 무결성 검사 완료: 아카이브에 손상이 없으며 정상입니다.');
      } else {
        alert('❌ 아카이브 손상 감지: ' + res.error);
      }
    });
  };

  // [추가]
  document.getElementById('btnToolAdd').onclick = () => {
    if (!AppState.currentArchiveInfo || !AppState.pyBridge) return;
    AppState.pyBridge.selectSourceFiles((pathsJson) => {
      const paths = JSON.parse(pathsJson);
      if (paths && paths.length > 0) {
        showProgress('파일 추가 중...', '아카이브를 갱신하고 있습니다.');
        AppState.pyBridge.addFilesToArchive(AppState.currentArchiveInfo.file_path, pathsJson, (resJson) => {
          hideProgress();
          const res = JSON.parse(resJson);
          if (res.success) {
            openArchiveFile(AppState.currentArchiveInfo.file_path);
          } else {
            alert('파일 추가 실패: ' + res.error);
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
      alert('삭제할 파일을 먼저 체크박스로 선택해주세요.');
      return;
    }
    if (!confirm(`선택한 ${selItems.length}개 항목을 아카이브에서 삭제하시겠습니까?`)) return;

    showProgress('파일 삭제 중...', '아카이브를 갱신하고 있습니다.');
    AppState.pyBridge.deleteFilesFromArchive(AppState.currentArchiveInfo.file_path, JSON.stringify(selItems), (resJson) => {
      hideProgress();
      const res = JSON.parse(resJson);
      if (res.success) {
        openArchiveFile(AppState.currentArchiveInfo.file_path);
      } else {
        alert('파일 삭제 실패: ' + res.error);
      }
    });
  };

  // [코드페이지 모달]
  document.getElementById('btnToolCodePage').onclick = openCodePageModal;
  document.getElementById('btnCloseCodePage').onclick = closeCodePageModal;
  document.getElementById('btnApplyCodePage').onclick = () => {
    const checkedRad = document.querySelector('input[name="radEncoding"]:checked');
    if (checkedRad) {
      AppState.selectedEncoding = checkedRad.value;
      const labelMap = {
        'auto': '코드페이지',
        'cp949': '한국어 (CP949)',
        'utf-8': 'UTF-8',
        'shift_jis': '일본어 (SJIS)',
        'gbk': '중국어 (GBK)',
        'raw': '원본 (Raw)'
      };
      const encTitle = labelMap[AppState.selectedEncoding] || '자동 감지';
      const btn = document.getElementById('btnToolCodePage');
      btn.setAttribute('data-tooltip', `코드페이지: ${encTitle}`);
      btn.setAttribute('title', `코드페이지: ${encTitle}`);
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

  document.getElementById('selPresetMode').onchange = (e) => {
    const val = e.target.value;
    const selFmt = document.getElementById('selCompressFmt');
    if (val === 'windows' || val === 'macos') selFmt.value = 'ZIP';
    else if (val === 'linux') selFmt.value = 'TAR.GZ';
    else if (val === 'ultra7z') selFmt.value = '7Z';
  };

  document.getElementById('btnCompressHere').onclick = () => {
    triggerCompress(false);
  };

  document.getElementById('btnCompressCustom').onclick = () => {
    triggerCompress(true);
  };

  function triggerCompress(changeFolder) {
    if (AppState.compressSourcePaths.length === 0) {
      alert('압축할 파일이나 폴더를 추가해주세요.');
      return;
    }

    const fmt = document.getElementById('selCompressFmt').value;
    const preset = document.getElementById('selPresetMode').value;
    const level = parseInt(document.getElementById('selCompressLevel').value, 10);
    const pwd = document.getElementById('txtCompressPwd').value;
    const splitMb = parseInt(document.getElementById('selSplitSize').value, 10);

    closeNewCompressModal();
    showProgress('압축 파일 생성 중...', '시스템별 최적화 압축을 진행하고 있습니다.');

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
            finishProgress(`아카이브 생성 완료: ${res.output_path}`, res.output_dir);
          } else {
            hideProgress();
            if (res.error && !res.error.includes("취소")) {
              alert('압축 생성 실패: ' + res.error);
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
    document.querySelectorAll('.item-chk').forEach(chk => {
      chk.checked = isChecked;
      chk.dispatchEvent(new Event('change'));
    });
  };

  document.addEventListener('click', (e) => {
    if (!e.target.closest('#archiveContextMenu')) hideArchiveContextMenu();
  });
  document.addEventListener('contextmenu', (e) => {
    if (!e.target.closest('#tblExplorerBody tr')) e.preventDefault();
  });
  window.addEventListener('blur', hideArchiveContextMenu);
  window.addEventListener('resize', hideArchiveContextMenu);
  document.getElementById('explorerGridContainer').addEventListener('scroll', hideArchiveContextMenu);

  // HTML5 Drag & Drop 이벤트 리스너
  window.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const dropZone = document.getElementById('homeDropZone');
    if (dropZone) dropZone.classList.add('dragover');
  });

  window.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const dropZone = document.getElementById('homeDropZone');
    if (dropZone) dropZone.classList.remove('dragover');
  });

  window.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const dropZone = document.getElementById('homeDropZone');
    if (dropZone) dropZone.classList.remove('dragover');

    // 전체 로컬 경로는 Qt 뷰의 네이티브 dropEvent에서 한 번만 전달한다.
  });
}

// --------------------------------------------------------------------------
// 9. 진입점
// --------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initIcons();
  initFloatingTooltips();
  initEvents();
  initNativeBridge();
  showHomeView();
});

/* v1.5 packaging UI. All filesystem actions go through the native bridge. */
const packText = (ko, en) => AppState.language === 'en' ? en : ko;
let toolPaths = [];
let lastToolText = '';

function packModal(id, title, content) {
  const node = document.createElement('div');
  node.id = id; node.className = 'layer-modal-backdrop';
  node.innerHTML = `<div class="compact-modal pack-modal"><div class="modal-header"><span class="modal-title">${title}</span><button class="modal-close-btn">×</button></div><div class="modal-body">${content}</div></div>`;
  node.querySelector('.modal-close-btn').onclick = () => node.classList.remove('active');
  document.body.append(node);
  return node;
}

function openPackTools(paths = [], action = 'convert') {
  toolPaths = [...paths];
  document.getElementById('packAction').value = action;
  document.getElementById('packPaths').textContent = toolPaths.join('\n');
  document.getElementById('packTools').classList.add('active');
  updateToolFields();
}

function updateToolFields() {
  const action = document.getElementById('packAction').value;
  document.querySelectorAll('.pack-tool-tab').forEach(button => {
    button.classList.toggle('active', button.dataset.action === action);
    button.setAttribute('aria-selected', String(button.dataset.action === action));
  });
  const descriptions = {
    convert: ['포맷 변환', '압축 파일을 ZIP, 7Z 또는 TAR 계열 형식으로 안전하게 변환합니다.'],
    batch: ['일괄 해제', '여러 압축 파일을 선택한 위치에 한 번에 풀어냅니다.'],
    cbz: ['CBZ 만들기', '이미지를 자연스러운 순서로 정리해 만화책용 CBZ를 만듭니다.'],
    privacy: ['개인정보 보호 압축', '파일 내용과 이름을 모두 숨기는 7Z AES 암호화 파일을 만듭니다.'],
    split: ['분할 압축', '큰 압축 파일을 선택한 크기의 번호 파일로 나눕니다.'],
  };
  const [title, copy] = descriptions[action] || descriptions.convert;
  document.getElementById('packToolTitle').textContent = title;
  document.getElementById('packToolDescription').textContent = copy;
  document.querySelectorAll('[data-actions]').forEach(el => {
    el.hidden = !el.dataset.actions.split(' ').includes(action);
  });
  document.querySelectorAll('#packFormat option').forEach(option => {
    option.disabled = action === 'split' && !['ZIP', '7Z'].includes(option.value);
  });
  if (action === 'split' && !['ZIP', '7Z'].includes(document.getElementById('packFormat').value)) {
    document.getElementById('packFormat').value = 'ZIP';
  }
}

window.validateSecurity = () => {
  const security = document.getElementById('securityMode').value;
  const pwd = document.getElementById('txtCompressPwd').value;
  if (security !== 'none' && (!pwd || pwd !== document.getElementById('passwordConfirm').value)) {
    alert(packText('비밀번호와 확인 값이 일치해야 합니다.', 'Enter matching passwords.')); return false;
  }
  if (security !== 'none') document.getElementById('selCompressFmt').value = security === 'private' ? '7Z' : 'ZIP';
  if (security === 'none') document.getElementById('txtCompressPwd').value = '';
  return true;
};

const originalOpenArchive = openArchiveFile;
openArchiveFile = function(path) {
  if (!AppState.pyBridge) return;
  AppState.archivePassword = '';
  AppState.pyBridge.listArchive(path, '', AppState.selectedEncoding === 'auto' ? '' : AppState.selectedEncoding, raw => {
    const info = JSON.parse(raw);
    if (!info.error) {
      if (info.items.some(item=>item.is_encrypted)) {
        AppState.pyBridge.requestPassword(packText('암호화된 파일의 비밀번호', 'Encrypted archive password'), pwd=>{AppState.archivePassword=pwd;showExplorerView(info);});
      } else showExplorerView(info);
      return;
    }
    AppState.pyBridge.requestPassword(packText('암호가 있는 파일이면 비밀번호를 입력하세요.', 'Enter the archive password, if encrypted.'), pwd => {
      if (!pwd) { alert(info.error); return; }
      AppState.pyBridge.listArchive(path, pwd, '', result => {
        const retry = JSON.parse(result);
        if (retry.error) { alert(retry.error); return; }
        AppState.archivePassword = pwd; showExplorerView(retry);
      });
    });
  });
};
const previousDrop = handleDroppedFiles;
handleDroppedFiles = function(paths) {
  if (!AppState.pyBridge) { window.pendingNativeDrop=paths; return; }
  if (paths.length > 1 && paths.every(p => /\.(zip|7z|rar|alz|egg|tar|gz|bz2|xz|cab|iso|cbz)$/i.test(p))) {
    openPackTools(paths, 'batch'); return;
  }
  if (paths.length === 1 && /\.cbz$/i.test(paths[0])) { openArchiveFile(paths[0]); return; }
  previousDrop(paths);
};
window.handleNativeDrop = window.handleDroppedFiles = handleDroppedFiles;

document.addEventListener('DOMContentLoaded', () => {
  const tools = packModal('packTools', '도구', `
    <input type="hidden" id="packAction" value="convert">
    <div class="pack-tool-tabs" role="tablist" aria-label="도구 선택">
      ${[['convert','convert','포맷 변환'],['batch','batch','일괄 해제'],['cbz','cbz','CBZ 만들기'],['privacy','privacy','개인정보 보호'],['split','split','분할 압축']].map(([action,icon,label])=>`<button class="pack-tool-tab" data-action="${action}" role="tab"><span class="pack-tool-icon">${window.CrowIcons[icon]}</span><span>${label}</span></button>`).join('')}
    </div>
    <div class="pack-tool-intro"><strong id="packToolTitle"></strong><span id="packToolDescription"></span></div>
    <div class="pack-row"><button class="btn" id="packSelect">파일 선택 / Files</button><button class="btn" id="packFolder">폴더 추가 / Folder</button><button class="btn" id="packClear">비우기 / Clear</button></div>
    <pre id="packPaths" class="pack-result"></pre>
    <div class="pack-options-grid">
    <label data-actions="convert split">출력 형식 / Output<select class="form-control" id="packFormat">${['ZIP','7Z','TAR','TAR.GZ','TAR.BZ2','TAR.XZ'].map(x=>`<option>${x}</option>`).join('')}</select></label>
    <label data-actions="convert batch">원본 비밀번호 / Source password<input type="password" id="packPassword" class="form-control" autocomplete="off"></label>
    <label data-actions="convert privacy">새 비밀번호 / New password<input type="password" id="packOutputPassword" class="form-control" autocomplete="off"></label>
    <label data-actions="privacy">비밀번호 확인 / Confirm<input type="password" id="packToolPasswordConfirm" class="form-control" autocomplete="off"></label>
    <label data-actions="batch">해제 방식 / Mode<select id="packMode" class="form-control"><option value="new_folder">각각 별도 폴더 / Separate folders</option><option value="current">현재 폴더 / Current folder</option><option value="smart">알아서 풀기 / Smart</option></select></label>
    <label data-actions="split">분할 크기 / Volume size<select id="packSplitSize" class="form-control"><option value="10">10 MB</option><option value="50">50 MB</option><option value="100" selected>100 MB</option><option value="500">500 MB</option><option value="1024">1 GB</option></select></label>
    <label data-actions="cbz" class="pack-check"><input type="checkbox" id="packRenumber" checked> 페이지 번호로 이름 정리 / Number pages</label>
    </div>
    <button id="packRun" class="btn primary">실행 / Run</button>
    <pre id="packResult" class="pack-result" role="status"></pre><button id="packCopy" class="btn">결과 복사 / Copy result</button>`);
  const settings = packModal('packSettings', '설정', `
    <section class="settings-section"><h3>화면</h3><div id="packGeneral"></div></section>
    <section class="settings-section"><h3>Windows 연결</h3>
      <div class="settings-action-row"><div><strong>압축 파일 기본 앱</strong><span id="packAssociations">현재 연결 상태 확인 중</span></div><button class="btn" id="packDefaults">설정 열기</button></div>
      <div class="settings-action-row"><div><strong>탐색기 우클릭 메뉴</strong><span>압축 및 해제 명령을 표시합니다.</span></div><div class="pack-row"><button class="btn" id="packShellOn">사용</button><button class="btn" id="packShellOff">해제</button></div></div>
    </section>
    <section class="settings-section"><h3>업데이트</h3>
      <div class="settings-action-row"><div><strong>Crow Pack v1.5.0</strong><label class="plain-check"><input type="checkbox" id="packAutoUpdate"> 시작할 때 확인</label></div><div id="packUpdateButton"></div></div>
    </section>`);
  document.getElementById('packGeneral').append(document.querySelector('#modalInfoApp .settings-panel'));
  document.getElementById('packUpdateButton').append(document.getElementById('btnToolUpdate'));
  document.querySelector('#packGeneral .settings-title').textContent='언어와 테마';
  const updateButton=document.getElementById('btnToolUpdate');updateButton.className='btn';updateButton.innerHTML='업데이트 확인';
  document.getElementById('btnToolAssociations').remove();
  const nav = document.getElementById('navGroupHome');
  for (const [id, label, icon, modal] of [['packToolsButton','도구','tools',tools],['packSettingsButton','설정','settings',settings]]) {
    const b = document.createElement('button'); b.id=id; b.className='tool-icon-btn';
    b.innerHTML = `${window.CrowIcons[icon] || ''}<span class="tool-btn-label">${label}</span>`;
    b.onclick=()=>{ modal.classList.add('active'); if(modal===settings && AppState.pyBridge) AppState.pyBridge.integrationStatus(r=>{const rows=JSON.parse(r),assigned=rows.filter(x=>x.handler).length;document.getElementById('packAssociations').textContent=`${rows.length}개 형식 중 ${assigned}개에 기본 앱이 지정됨`;}); };
    nav.insertBefore(b, document.getElementById('btnToolInfo'));
    b.querySelector('.tool-btn-label').dataset.i18n = id;
    b.dataset.tooltip = label;
  }
  TRANSLATIONS.ko.packToolsButton='도구'; TRANSLATIONS.en.packToolsButton='Tools';
  TRANSLATIONS.ko.packSettingsButton='설정'; TRANSLATIONS.en.packSettingsButton='Settings';
  TRANSLATIONS.ko['nav.info']='도움말'; TRANSLATIONS.en['nav.info']='Help';
  TRANSLATIONS.ko['info.title']='도움말'; TRANSLATIONS.en['info.title']='Help';
  TRANSLATIONS.ko['info.help'] += '<br>• 개인정보 보호: 7Z 파일 내용·이름 암호화. 비밀번호는 다른 수단으로 전달하세요.<br>• 목록에서 파일을 잡아 Explorer 폴더로 끌면 선택 항목을 복사합니다. 큰 파일은 준비가 필요합니다.<br>• 도구에서 포맷 변환, 일괄 해제, CBZ 생성, 개인정보 보호 및 분할 압축을 실행합니다.<br>• CBZ: 순서 있는 이미지 문서용 ZIP. ZIP/7Z/RAR/TAR/ALZ/EGG/CAB/ISO 지원.';
  TRANSLATIONS.en['info.help'] += '<br>• Privacy: encrypted 7Z contents and names. Share the password separately.<br>• Drag selected archive items into Explorer to copy them. Large files need preparation.<br>• Tools: format conversion, SHA-256 calculation/verification, ordered-image CBZ, batch extraction.';
  document.getElementById('btnToolInfo').removeAttribute('title');
  document.getElementById('btnToolInfo').dataset.tooltip='도움말 / Help';
  applyLanguage(AppState.language);
  const pwd = document.getElementById('txtCompressPwd');
  pwd.insertAdjacentHTML('beforebegin', `<label>보안 수준 / Security<select id="securityMode" class="form-control"><option value="none">암호 없음 / None</option><option value="zip">일반 암호 보호 / ZIP AES-256</option><option value="private">개인정보 보호 / Private 7Z</option></select></label><p id="securityNote" class="preset-note"></p>`);
  pwd.insertAdjacentHTML('afterend', `<input type="password" id="passwordConfirm" class="form-control" placeholder="비밀번호 확인 / Confirm password" autocomplete="off"><div class="pack-row"><button class="btn" id="passwordShow">표시 / Show</button><button class="btn" id="passwordRandom">자동 생성 / Random</button><button class="btn" id="passwordPhrase">패스프레이즈 / Phrase</button><button class="btn" id="passwordCopy">복사 / Copy</button></div><span id="passwordStrength" role="status"></span>`);
  const confirmation = document.getElementById('passwordConfirm');
  const strength=()=> { const length=pwd.value.length; document.getElementById('passwordStrength').textContent=packText(length>=20?'강함':length>=12?'보통':'짧음',length>=20?'Strong':length>=12?'Moderate':'Short')+' · '+packText(pwd.value && pwd.value===confirmation.value?'일치':'불일치',pwd.value && pwd.value===confirmation.value?'Match':'Mismatch'); };
  pwd.oninput=confirmation.oninput=strength;
  const security=()=> { const mode=document.getElementById('securityMode').value; pwd.disabled=confirmation.disabled=mode==='none'; if(mode!=='none')document.getElementById('selCompressFmt').value=mode==='private'?'7Z':'ZIP'; document.getElementById('securityNote').textContent=mode==='private'?'7Z AES + Header Encryption: 파일 내용·파일명·폴더명 보호 / Contents and names protected':mode==='zip'?'ZIP AES-256은 파일 내용은 보호하지만 내부 파일 이름은 숨기지 않습니다. / Contents encrypted; names remain visible.':''; };
  document.getElementById('securityMode').onchange=security; security();
  document.getElementById('passwordShow').onclick=()=>{pwd.type=confirmation.type=pwd.type==='password'?'text':'password';};
  for(const [id, mode] of [['passwordRandom','random'],['passwordPhrase','phrase']])document.getElementById(id).onclick=()=>AppState.pyBridge?.generatePassword(mode, value=>{pwd.value=confirmation.value=value;strength();});
  document.getElementById('passwordCopy').onclick=()=>AppState.pyBridge?.copyText(pwd.value);
  document.querySelectorAll('.pack-tool-tab').forEach(button=>button.onclick=()=>{document.getElementById('packAction').value=button.dataset.action;updateToolFields();});
  updateToolFields();
  const refresh=()=>document.getElementById('packPaths').textContent=toolPaths.join('\n');
  document.getElementById('packSelect').onclick=()=>AppState.pyBridge?.selectSourceFiles(r=>{toolPaths.push(...JSON.parse(r));refresh();});
  document.getElementById('packFolder').onclick=()=>AppState.pyBridge?.selectSourceFolder(r=>{toolPaths.push(...JSON.parse(r));refresh();});
  document.getElementById('packClear').onclick=()=>{toolPaths=[];refresh();};
  document.getElementById('packCopy').onclick=()=>AppState.pyBridge?.copyText(lastToolText);
  document.getElementById('packDefaults').onclick=()=>AppState.pyBridge?.openDefaultApps();
  for(const [id,enabled] of [['packShellOn',true],['packShellOff',false]])document.getElementById(id).onclick=()=>AppState.pyBridge?.setShellIntegration(enabled,r=>{const x=JSON.parse(r);alert(x.success?'완료 / Done':x.error);});
  const auto=document.getElementById('packAutoUpdate');auto.checked=loadPreference('autoUpdate','false')==='true';auto.onchange=()=>savePreference('autoUpdate',String(auto.checked));
  document.getElementById('packRun').onclick=()=>{
    if(!toolPaths.length || !AppState.pyBridge)return;
    const action=document.getElementById('packAction').value;
    const value=id=>document.getElementById(id).value;
    if(action==='convert' && toolPaths.length!==1){alert('파일 한 개를 선택하세요. / Select one file.');return;}
    if(action==='privacy' && (!value('packOutputPassword') || value('packOutputPassword')!==value('packToolPasswordConfirm'))){alert('비밀번호와 확인 값이 일치해야 합니다.');return;}
    document.getElementById('packRun').disabled=true;
    document.getElementById('packResult').textContent='처리 중 / Working…';
    AppState.pyBridge.runTool(JSON.stringify({action,paths:toolPaths,format:value('packFormat'),password:value('packPassword'),outputPassword:value('packOutputPassword'),mode:value('packMode'),splitSize:value('packSplitSize'),renumber:document.getElementById('packRenumber').checked}));
    document.getElementById('packPassword').value=document.getElementById('packOutputPassword').value=document.getElementById('packToolPasswordConfirm').value='';
  };
  const timer=setInterval(()=>{
    if(!AppState.pyBridge)return;clearInterval(timer);
    AppState.pyBridge.toolFinished.connect(raw=>{const result=JSON.parse(raw);document.getElementById('packRun').disabled=false;
      if(!result.success)lastToolText=result.cancelled?'취소 / Cancelled':result.error;
      else if(result.action==='batch'){const ok=result.result.filter(x=>x.success).length;lastToolText=`성공 / Success: ${ok} · 실패 / Failed: ${result.result.length-ok}\n`+result.result.map(x=>`${x.success?'✓':'✕'} ${x.path}\n${x.error || x.output_dir}`).join('\n');}
      else lastToolText=String(result.result);
      document.getElementById('packResult').textContent=lastToolText;
    });
    AppState.pyBridge.progressEvent.connect((cur,total,name)=>{if(document.getElementById('packRun').disabled)document.getElementById('packResult').textContent=`${cur} / ${total}\n${name}`;});
    if(auto.checked)AppState.pyBridge.checkForUpdates(raw=>{const result=JSON.parse(raw);if(result.update_available)alert(result.message || '새 버전이 있습니다. / An update is available.');});
    if(window.pendingShellAction)window.handleShellAction(...window.pendingShellAction);
    if(window.pendingNativeDrop){const paths=window.pendingNativeDrop;window.pendingNativeDrop=null;handleDroppedFiles(paths);}
  },100);
});

window.handleShellAction = (action,paths) => {
  if(!AppState.pyBridge || !document.getElementById('packTools')){window.pendingShellAction=[action,paths];return;}
  window.pendingShellAction=null;
  if(['zip','7z','private','compress'].includes(action)){
    addPathsToCompress(paths);openNewCompressModal();
    document.getElementById('selCompressFmt').value=action==='7z'||action==='private'?'7Z':'ZIP';
    document.getElementById('securityMode').value=action==='private'?'private':'none';
    document.getElementById('securityMode').dispatchEvent(new Event('change'));
  }else if(action==='open')openArchiveFile(paths[0]);
  else if(action==='test')AppState.pyBridge.testArchive(paths[0],'',r=>alert(r));
  else {openPackTools(paths,action.startsWith('convert')?'convert':'batch');if(action==='convert7z')document.getElementById('packFormat').value='7Z';if(action==='here')document.getElementById('packMode').value='current';if(action==='smart')document.getElementById('packMode').value='smart';}
};

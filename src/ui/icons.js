/**
 * Crow Pack - Crow Signature Vector Iconography (v1.0K)
 * 정통 칠흑의 까마귀(Crow/Raven) 본연의 흑요석 블랙 부리와 깃털 실루엣
 */

const CrowIcons = {
  // 정통 칠흑의 까마귀(Crow / Raven) 브랜드 로고
  logo: `
    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" class="crow-svg-icon">
      <defs>
        <linearGradient id="ravenBodyGrad" x1="15" y1="15" x2="85" y2="85" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#3b4252" />
          <stop offset="45%" stop-color="#1e232d" />
          <stop offset="100%" stop-color="#0a0c10" />
        </linearGradient>
        <linearGradient id="ravenWingGrad" x1="10" y1="30" x2="70" y2="90" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#4c566a" />
          <stop offset="50%" stop-color="#282e3a" />
          <stop offset="100%" stop-color="#10131a" />
        </linearGradient>
        <linearGradient id="ravenBeakDark" x1="60" y1="20" x2="96" y2="45" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#475569" />
          <stop offset="50%" stop-color="#1e293b" />
          <stop offset="100%" stop-color="#020617" />
        </linearGradient>
      </defs>

      <!-- 까마귀 꼬리 깃털 -->
      <path d="M12 75L22 62L28 72L16 86Z" fill="#10131a" stroke="#2e3440" stroke-width="1.2"/>
      <path d="M16 86L26 70L34 78L22 94Z" fill="#0a0c10" stroke="#2e3440" stroke-width="1.2"/>

      <!-- 까마귀 몸체 -->
      <path d="M22 62C20 45 28 28 44 20C55 14 68 15 72 24C74 27 75 32 72 36C68 42 56 46 48 54C38 64 30 76 22 88C20 84 21 72 22 62Z" 
            fill="url(#ravenBodyGrad)" stroke="#3b4252" stroke-width="1.5" stroke-linejoin="round"/>

      <!-- 웅장한 날개 -->
      <path d="M30 45C38 32 54 28 66 32C64 44 58 58 48 68C38 78 26 82 18 84C20 72 24 58 30 45Z" 
            fill="url(#ravenWingGrad)" stroke="#434c5e" stroke-width="1.5"/>
      <path d="M38 48C46 40 58 38 64 42" stroke="#4c566a" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M32 58C42 50 52 48 58 54" stroke="#3b4252" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M26 68C36 60 46 58 50 64" stroke="#2e3440" stroke-width="1.5" stroke-linecap="round"/>

      <!-- 머리 & 목 -->
      <path d="M52 18C62 14 74 16 78 26C80 32 78 38 74 42C68 46 58 44 52 38Z" 
            fill="url(#ravenBodyGrad)"/>
      <path d="M56 36C52 42 46 48 42 54" stroke="#4c566a" stroke-width="1.2" stroke-linecap="round"/>

      <!-- 검은 부리 -->
      <path d="M74 24L96 36C90 42 80 44 70 40L72 30Z" 
            fill="url(#ravenBeakDark)" stroke="#090d16" stroke-width="1.5" stroke-linejoin="round"/>
      <path d="M72 32Q85 35 96 36" stroke="#334155" stroke-width="1.2" stroke-linecap="round"/>
      <ellipse cx="76" cy="28" rx="1.5" ry="0.8" fill="#1e293b"/>

      <!-- 눈 -->
      <circle cx="64" cy="25" r="4" fill="#020617" stroke="#475569" stroke-width="1.2"/>
      <circle cx="64" cy="25" r="2" fill="#1e293b"/>
      <circle cx="65.2" cy="23.8" r="0.9" fill="#ffffff"/>
    </svg>
  `,

  // 압축 파일 열기
  openArchive: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
      <polygon points="12 11 12 17 17 14"/>
    </svg>
  `,

  // ISO 디스크 이미지 열기
  isoDisc: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="9"/>
      <circle cx="12" cy="12" r="2.5"/>
      <path d="M12 3a9 9 0 0 1 9 9"/>
      <path d="M5.6 18.4 9.5 14.5"/>
    </svg>
  `,

  isoCreate: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="10" cy="12" r="7.5"/>
      <circle cx="10" cy="12" r="2"/>
      <path d="M10 4.5a7.5 7.5 0 0 1 7.5 7.5"/>
      <path d="M19 15v6M16 18h6"/>
    </svg>
  `,

  pdfOptimize: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <path d="M8 15h8M10 12l-2 3 2 3M14 12l2 3-2 3"/>
    </svg>
  `,

  update: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="23 4 23 10 17 10"/>
      <polyline points="1 20 1 14 7 14"/>
      <path d="M3.5 9a9 9 0 0 1 14.9-3.4L23 10M1 14l4.6 4.4A9 9 0 0 0 20.5 15"/>
    </svg>
  `,

  association: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/>
      <path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>
    </svg>
  `,

  // 새로 압축하기
  newArchive: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
      <line x1="12" y1="8" x2="12" y2="16"/>
      <line x1="8" y1="12" x2="16" y2="12"/>
    </svg>
  `,

  // 이 폴더에 풀기 (Extract Here)
  extract: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  `,
  extractHere: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  `,

  // 폴더변경 풀기 (Extract Custom)
  extractCustom: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
      <polyline points="12 11 12 17 17 14"/>
    </svg>
  `,

  // 파일 추가
  addFile: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="12" y1="18" x2="12" y2="12"/>
      <line x1="9" y1="15" x2="15" y2="15"/>
    </svg>
  `,

  // 파일 삭제
  delete: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="3 6 5 6 21 6"/>
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
      <line x1="10" y1="11" x2="10" y2="17"/>
      <line x1="14" y1="11" x2="14" y2="17"/>
    </svg>
  `,

  // 무결성 테스트
  test: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      <polyline points="8 11 10 13 14 9"/>
    </svg>
  `,

  // 코드페이지
  codepage: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="2" y1="12" x2="22" y2="12"/>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </svg>
  `,

  // 취소 / 닫기
  cancel: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="15" y1="9" x2="9" y2="15"/>
      <line x1="9" y1="9" x2="15" y2="15"/>
    </svg>
  `,

  // 정보 & 설정
  info: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="16" x2="12" y2="12"/>
      <line x1="12" y1="8" x2="12.01" y2="8"/>
    </svg>
  `,

  // 폴더
  folder: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
    </svg>
  `,

  // 상위 폴더 이동
  folderUp: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
      <polyline points="12 10 12 16"/>
      <polyline points="9 13 12 10 15 13"/>
    </svg>
  `,

  // 파일
  file: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
    </svg>
  `
};

window.CrowIcons = CrowIcons;

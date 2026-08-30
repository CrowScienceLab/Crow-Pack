/**
 * Crow Pack - Crow Signature Vector Iconography (v1.1.0)
 * 정통 칠흑의 까마귀(Crow/Raven) 본연의 흑요석 블랙 부리와 깃털 실루엣
 */

const CrowIcons = {
  // 땅에 앉아 오른쪽을 바라보는 현실적인 검은 까마귀 브랜드 로고
  logo: `
    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" class="crow-svg-icon">
      <defs>
        <linearGradient id="ravenBodyGrad" x1="34" y1="20" x2="69" y2="84" gradientUnits="userSpaceOnUse">
          <stop stop-color="#354052"/><stop offset=".45" stop-color="#141a24"/><stop offset="1" stop-color="#030508"/>
        </linearGradient>
      </defs>
      <ellipse cx="49" cy="90" rx="39" ry="4" fill="#05070b" opacity=".45"/>
      <path d="M18 77 8 87l24-6 9-10z" fill="#070a0f" stroke="#31394a" stroke-width="1"/>
      <path d="M24 73c-2-19 5-38 20-47 9-6 20-7 29-3 6 3 10 8 11 15 1 10-6 16-14 22-4 3-6 8-6 13 0 8 4 12 10 16H34c-7-3-10-8-10-16z" fill="url(#ravenBodyGrad)" stroke="#05070b" stroke-width="1.6"/>
      <path d="M31 52c8-15 25-22 39-16-1 16-8 32-20 42-8 7-18 10-28 9 8-9 7-23 9-35z" fill="#111722" stroke="#3b4659" stroke-width="1.2"/>
      <path d="M38 48c9-7 19-10 28-7M33 59c10-7 20-9 29-5M29 70c10-5 19-6 27-2" stroke="#445064" stroke-width="1" stroke-linecap="round" opacity=".75"/>
      <path d="M79 30 98 38c-6 5-13 7-21 5l-4-7z" fill="#05070a" stroke="#364155" stroke-width="1"/>
      <circle cx="76" cy="31" r="2.4" fill="#080b10" stroke="#59677b" stroke-width="1"/>
      <circle cx="76.7" cy="30.3" r=".7" fill="#dbeafe"/>
      <path d="M40 86v6m-4 0h10m15-6v6m-4 0h10" stroke="#080b10" stroke-width="2.4" stroke-linecap="round"/>
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

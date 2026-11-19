# CrowPack 1.7 검토 및 배포 기록

2026-11-19 · Windows 11 x64 · Python 3.12.14 · Qt 6.11.2

기존 1.6.1 작업 트리에 AGY의 Command Hub 디자인을 유지한 채 후속 수정했습니다. 앱과 공개 태그는 `1.7`과 `v1.7`, Windows EXE 파일 버전과 Store 매니페스트는 `1.7.0.0`입니다. Microsoft Store 제품 ID `9NPBKL0XTKQ7`과 기존 설치 AppId를 유지했습니다. 이번 작업에서 확인한 GitHub 공개 최신 태그는 `v1.6.0`입니다.

## 적용 사항

- 설치본 첫 실행과 앱 설정에서 지원 확장자별 기본 앱을 확인하고 Windows 기본 앱 설정으로 바로 이동합니다. GitHub 설치 시 사용자 선택과 기존 Windows 연결을 유지하며, 연결이 없는 형식에만 레거시 등록을 시도합니다. Store는 매니페스트에서 15개 확장자를 후보로 등록합니다.
- GitHub 설치 프로그램은 바탕화면 바로가기 옵션을 기본 선택합니다. Store판은 사용자가 첫 실행 또는 설정에서 요청할 때 앱 ID 기반 바로가기를 만듭니다. 이미 있는 다른 바로가기는 덮어쓰지 않습니다.
- 진행·완료, 주요 오류·확인 제목, 인코딩, PDF 분석·최적화 안내와 앱 제공 파일 대화상자 제목을 한영으로 표시합니다. 파일 대화상자의 취소 상태를 명시하고 기존 상세 오류는 원문으로 유지합니다.
- Qt WebChannel 페이지는 번들 `index.html`로 제한합니다. 탐색기 셸 명령 전달에서 명령 이름과 메시지 형식 및 길이를 확인합니다.
- RAR 해제에는 공통 해제 경로 검사와 크기 제한 스트림을 사용합니다. 아카이브 출력 경로의 링크·정션과 Windows 예약 이름 검사를 강화했습니다.
- GitHub 업데이트는 응답 크기·형식, 릴리스 설치 파일의 경로·크기·해시를 확인합니다. Store판 설정은 Microsoft Store를 직접 엽니다. 두 설치 채널의 업데이트는 별도로 관리됩니다.
- Crow Science Lab 저작권 및 원본 출처를 앱 도움말, 바이너리 속성, 소스 헤더와 배포 패키지의 `NOTICE.md`에 표시합니다. 허락된 수정·재배포 시 유지할 출처와 변경 정보는 `NOTICE.md`에 기록했습니다.

## 검증

| 항목 | 결과 |
| --- | --- |
| `unittest` / Ruff | 단위 테스트 71개 통과, Ruff 경고 0건 |
| PyPI `pip-audit --local --skip-editable` | pypdf·msgpack에 발견된 취약점 8건을 수정 버전으로 갱신했습니다. pywin32를 포함한 현재 환경의 알려진 취약점 0건 |
| Qt WebEngine | 설정·DOM·드래그 회귀 통과. 실제 2쪽 PDF 분석과 한영 전환, 인코딩 및 진행·완료 상태, Windows 설정과 바로가기 요청 후 결과, Store 전용 업데이트 동작 확인 |
| Qt 레이아웃 | 기존 126개 매트릭스를 `QT_SCALE_FACTOR=1`, `1.5`에서 각 실행. 모두 통과 |
| 실제 압축 파일 | RAR3·RAR5의 저장 방식 항목 선택 해제 후 바이트 비교 통과. Windows makecab/expand CAB 왕복 통과 |
| 컴파일된 EXE | Windows 기본 Qt 보안 설정에서 `--smoke-test` 결과 버전 `1.7`, `ui_ready=true`. 파일 속성 `1.7.0.0` 및 저작권 확인 |
| Windows Shell 바로가기 | 임시 폴더에 EXE 및 Store 앱 ID 링크를 실제 생성. GitHub 링크의 대상과 아이콘 경로가 1.7 빌드와 일치하고, Store 링크는 이 PC에 설치된 `1.6.0.0`을 실행. 같은 요청을 반복하면 기존 링크를 인식 |
| Store MSIX | 패키지 무결성, 매니페스트의 확장자 15개와 기존 앱 ID, Store PNG 85개 및 PRI, Shell 모듈과 저작권 고지를 확인 |

## 로컬 산출물

- `release/CrowPack-v1.7-Setup-x64.exe`
- `release/CrowPack-v1.7-Portable-x64.zip`
- `release/CrowPack-v1.7-Source.zip`
- `release/CrowPack-v1.7-Store-x64.msix`
- `release/SHA256SUMS.txt`

Store MSIX는 Partner Center 제출용 서명 전 패키지입니다. MakePRI는 Store 아이콘 85개를 인덱싱했고, 빈 `packaging` 설정 노드 경고를 출력했습니다.

GitHub 릴리스 본문과 Microsoft Store의 전체 제품 설명, 주요 기능, 새 기능은 [1.7 배포 소개](LISTINGS-1.7.md)에 한국어와 영어로 준비했습니다.

## 남은 확인 범위

- 도움말은 Qt 오프스크린 780×520, DPR 1에서 본문 `scrollHeight 403` / `clientHeight 391`로 12px 스크롤이 확인됐습니다. 내용은 스크롤로 읽을 수 있습니다. 도움말 간격 조정과 인앱 확인창의 디자인·접근성 검토는 AGY 후속 과제입니다.
- Windows 셸 메뉴의 등록 문구는 한국어이며, OS 제공 대화상자 버튼의 언어는 Windows 설정을 따릅니다. Explorer의 실제 드롭 완료와 Store를 통한 1.7 설치·업데이트 검증은 남아 있습니다.
- 압축 방식 RAR의 외부 백엔드, ALZ/EGG 변형 및 CAB 변형별 호환성은 추가 확인이 필요합니다. CAB는 Windows `expand`가 임시 폴더에서 먼저 처리하는 형식이므로 공통 스트림 해제에 적용되는 크기 제한과 검증 범위가 다릅니다.
- GitHub 공개 및 Store 제출은 수행하지 않았습니다.

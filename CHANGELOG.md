# Changelog

## [1.5.0]

- 개인정보 보호 7Z AES 및 헤더 암호화, 비밀번호 확인·생성·복사 UI.
- 자연 정렬과 페이지 번호를 지원하는 CBZ 생성, ZIP 엔진 기반 탐색·해제.
- 안전한 임시 해제 및 결과 검사 기반 포맷 변환과 분할 압축 도구.
- 별도 폴더·스마트·현재 폴더 일괄 해제와 파일별 성공/실패 보고.
- ArchiveManager를 통한 Qt 네이티브 Explorer drag export와 세션 임시 파일 관리.
- 풀다운 없이 다섯 기능을 노출하는 도구 화면과 아이콘 없는 목록형 설정 화면.
- 대칭형 까마귀/패키지 고해상도 앱 아이콘 및 포맷 배지.
- HKCU 파일 연결, 클래식 Explorer 메뉴, 공식 기본 앱 설정 링크 및 설치/제거 등록.
- ALZ/EGG 선택 해제 지원과 기존 압축·ISO·PDF 기능 회귀 검사.

## [1.1.0] - 2026-08-31

### Added

- All archive entries are selected by default, with Shift-range, Ctrl-toggle, and right-button drag selection.
- PDF size analysis with image, font, attachment, document-type, and recommended-preset reporting.
- Extreme local PDF compression that rebuilds visible pages as adaptive 120 DPI images after a loss warning.
- Windows `Applications\\CrowPack.exe` supported-type registration and automatic association for unclaimed formats.

### Changed

- Replaced the Windows and in-app brand art with a grounded side-profile black crow.
- Expanded lossy PDF optimization to low-colour, monochrome, palette, and transparent images.
- PDF results now report actual reduction percentage, processed images, skipped images, and rasterized pages.

### Security

- PDF analysis and all five compression presets remain local-only and never upload document contents.
- Encrypted and digitally signed PDFs remain protected; extreme mode explicitly warns about removed document features.

## [1.0K] - 2026-08-29

### Added

- ISO 9660 level 3 data-image creation with Joliet and Rock Ridge names.
- Four PDF size-reduction presets: lossless, high quality, balanced, and compact.
- Per-user Windows installer with Start Menu and optional desktop shortcuts.
- Live GitHub release update checks.
- One ISO Image window with Read (default) and Create tabs, including ISO drag-and-drop.
- Korean/English UI selection and Black, Bright Skyblue, and White Pink themes.
- A black-crow-on-disc Windows application and file-association icon.

### Fixed

- Removed the delayed second browser tooltip while retaining accessible labels.
- Connected every ISO/PDF modal control and expanded UI smoke coverage for all buttons.
- Corrected photo classification so downsampled colour sampling does not skip photographic images.
- Converted Windows launch/build scripts to CRLF so `cmd.exe` reads every command reliably.
- Unified and visibly labelled the ISO, PDF, update, file-association, and help toolbar buttons.

### Security

- ISO and PDF outputs use validated temporary files and never overwrite existing files.
- PDF optimization refuses encrypted or digitally signed documents.

## [1.0d] - 2026-08-28

### Added

- Custom archive context menu with bounded image thumbnails and safe copy-out actions.
- ZIP-only delete and move-out actions; ISO and other read-only formats remain copy-only.
- Lossless PDF stream and duplicate-object optimization with signature protection.
- Home-toolbar update status and Windows per-user file-association controls.

### Fixed

- Checkbox clicks no longer toggle twice through the containing table row.
- Native file drags restore the neon drop-zone feedback through a Qt-to-JavaScript signal.
- Disabled Chromium's unrelated `View page source` context menu.

### Changed

- Expanded directory selection to include descendant archive entries.

## [1.0.0] - 2026-08-28

### Added

- Read-only ISO image browsing and safe file copying for ISO 9660, Joliet, Rock Ridge, and UDF bridge images.
- A dedicated ISO-open button on the home toolbar.

### Fixed

- Native file drops now retain their absolute Windows paths when dropped on the WebEngine home view.

### Removed

- The redundant new-compression toolbar button.
- File-association registration and update-check controls from the information dialog.

## [0.9.0] - 2026-08-28

### Added

- AES-256 ZIP encryption through `pyzipper` 0.4.0 or newer.
- Shared extraction policy for traversal, link, collision, and decompression-bomb protection.
- Security regression tests and GitHub Actions checks.
- Release metadata, dependency bounds, security policy, and repository hygiene files.

### Changed

- Restricted the privileged Qt WebEngine page to bundled local resources.
- Rendered archive-controlled names as text instead of HTML.
- Replaced shell-based Windows commands with argument-safe process calls.
- Updated minimum secure versions for `py7zr` and `rarfile`.
- Standardized the public version label as `v0.9.0`.

### Removed

- Legacy Crow Press launch and one-time folder rename scripts.
- Python bytecode and cache artifacts from the release tree.

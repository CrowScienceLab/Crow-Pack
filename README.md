# Crow Pack v1.0K

Crow Pack은 Windows 10/11용 압축 파일 생성·해제 및 ISO 이미지 탐색·생성 데스크톱
앱입니다. 한국어 파일명 정규화와 로컬 전용 PySide6 WebEngine UI를 제공합니다.

- 제작: `Crow Science Lab`
- 플랫폼: Windows 10/11 64-bit
- Python: 3.10~3.14

## 지원 범위

| 포맷 | 목록 | 해제 | 생성 | 비고 |
|---|---:|---:|---:|---|
| ZIP | O | O | O | AES-256 비밀번호 지원 |
| 7Z | O | O | O | AES 암호화, `py7zr>=1.1.3` |
| TAR/GZ/BZ2/XZ | O | O | O | 링크 및 특수 파일 차단 |
| RAR | O | O | - | `rarfile` 외부 백엔드 필요 |
| CAB | 제한 | O | - | Windows `expand.exe` 사용 |
| ALZ/EGG | O | 실험적 | - | 일부 변형·분할·암호화 파일 미지원 |
| ISO | O | 파일 복사 | O | 데이터 ISO 생성(ISO 9660/Joliet/Rock Ridge), 부팅 ISO 제외 |

`DOCX`, `XLSX`, `PPTX`, `JAR`, `APK`처럼 ZIP 기반인 파일도 열 수 있습니다.

아카이브 목록의 우클릭 메뉴에서 그림 미리보기와 파일 복사를 사용할 수 있습니다.
ZIP은 삭제 및 폴더로 이동을 추가 지원하며, ISO와 기타 읽기 전용 형식은 복사만 지원합니다.
초기 화면의 `ISO 이미지` 버튼은 기본 읽기 탭과 만들기 탭을 한 창에 제공하며, 읽기 탭에
ISO 파일을 직접 끌어다 놓을 수 있습니다. `PDF 용량 조절` 버튼은
무손실·고화질·균형(권장)·최소 용량의 네 프리셋을 제공합니다.
텍스트와 벡터는 유지하고, 손실 프리셋에서는 큰 사진 이미지만 자동 축소·재압축합니다.
전자서명 또는 암호화된 PDF는 원본 보호를 위해 변경하지 않습니다.

`정보와 사용법`에서 한국어/English를 선택하고 Black(기본), Bright Skyblue, White Pink
화면 테마를 바꿀 수 있습니다. 선택은 현재 Windows 사용자에게 저장됩니다. 앱과 파일 연결
아이콘은 디스크 위 검은 까마귀 디자인을 사용합니다.

## 설치와 실행

Python 3.12 설치를 권장합니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe main.py
```

설치 후에는 `Crow_Pack.bat`로도 실행할 수 있습니다.

## 테스트

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip_audit
```

## EXE와 Windows 설치본 빌드

`build_exe.bat`를 실행하면 `dist\CrowPack\CrowPack.exe`가 만들어집니다. 빌드 머신에서
생성된 EXE를 먼저 Windows Defender와 VirusTotal 등으로 검사하고, 깨끗한 가상 머신에서
압축 생성·해제와 ISO 파일 복사를 확인한 뒤 배포하세요.

Inno Setup 6을 설치한 뒤 `build_installer.bat`를 실행하면
`release\CrowPack-v1.0K-Setup-x64.exe` 설치본이 만들어집니다. 설치는 현재 사용자 영역에
진행되므로 관리자 권한이 필요하지 않으며 시작 메뉴와 선택형 바탕 화면 바로가기를 제공합니다.

## 보안 동작

- 절대 경로, `..`, 링크, Windows 예약 파일명과 경로 충돌을 차단합니다.
- 항목 수·단일 파일·전체 해제 크기·압축률 제한으로 압축 폭탄 위험을 줄입니다.
- 아카이브의 파일명은 HTML로 실행하지 않고 텍스트로 렌더링합니다.
- 실행 파일과 스크립트는 아카이브 미리보기에서 바로 실행하지 않습니다.
- 기존 출력 아카이브는 묵시적으로 덮어쓰지 않습니다.
- ISO와 PDF 결과도 원본을 덮어쓰지 않고, 임시 파일 검증 후 최종 이름으로 이동합니다.
- 앱은 파일을 외부 서버로 전송하지 않습니다.

자세한 신고 절차와 제한은 [SECURITY.md](SECURITY.md)를 참고하세요.

## 릴리스 전 체크리스트

- 모든 테스트와 `pip-audit` 통과
- Windows 10/11 깨끗한 환경에서 EXE 스모크 테스트
- RAR 백엔드를 사용할 경우 UnRAR/WinRAR 7.23 이상 확인
- `dist` 결과물의 SHA-256 체크섬 생성
- 저장소의 GitHub 비공개 보안 신고 기능 활성화
- 공개 라이선스 선택 후 `LICENSE` 추가
- Git 작성자 이메일이 공개 가능한 주소인지 확인

현재 소스에는 라이선스가 확정되어 있지 않습니다. 저작권자가 라이선스를 선택하기 전에는
제3자가 복제·수정·재배포할 수 있다고 가정하면 안 됩니다.

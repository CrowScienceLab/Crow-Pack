"""
Crow Pack - Encoding & Path Helper
한국어 인코딩(CP949, EUC-KR, UTF-8) 자동 판별 및 macOS NFD 한글 자소 정규화(NFC) 모듈
"""

import unicodedata

import chardet


def normalize_korean_text(text: str) -> str:
    """
    macOS 등에서 발생할 수 있는 NFD(자소 분리: ㅇㅏㄴㄴㅕㅇ)를 NFC(완성형: 안녕)로 정규화합니다.
    """
    if not text:
        return ""
    # NFC 정규화
    normalized = unicodedata.normalize('NFC', text)
    return normalized


def smart_decode_filename(raw_bytes: bytes, default_encoding: str = "cp949") -> str:
    """
    바이트 문자열을 분석하여 한국어 환경에 최적화된 인코딩으로 디코딩합니다.
    UTF-8 -> CP949 / EUC-KR -> 기본 인코딩 순으로 시도하며 chardet을 보조로 활용합니다.
    """
    if not raw_bytes:
        return ""

    # 1. UTF-8 시도 (가장 최신 표준)
    try:
        decoded = raw_bytes.decode('utf-8')
        # 유효한 문자열인지 확인 (깨진 문자 검사)
        return normalize_korean_text(decoded)
    except (UnicodeDecodeError, UnicodeError):
        pass

    # 2. CP949 시도 (한국 윈도우 표준)
    try:
        decoded = raw_bytes.decode('cp949')
        return normalize_korean_text(decoded)
    except (UnicodeDecodeError, UnicodeError):
        pass

    # 3. EUC-KR 시도
    try:
        decoded = raw_bytes.decode('euc-kr')
        return normalize_korean_text(decoded)
    except (UnicodeDecodeError, UnicodeError):
        pass

    # 4. chardet으로 추정
    detected = chardet.detect(raw_bytes)
    encoding = detected.get('encoding')
    if encoding:
        try:
            decoded = raw_bytes.decode(encoding)
            return normalize_korean_text(decoded)
        except (UnicodeDecodeError, UnicodeError):
            pass

    # 5. 최종 대체 (errors='replace')
    try:
        return normalize_korean_text(raw_bytes.decode(default_encoding, errors='replace'))
    except Exception:
        return normalize_korean_text(raw_bytes.decode('latin-1', errors='replace'))


def fix_zip_filename(filename: str, flag_bits: int = 0) -> str:
    """
    ZIP 파일의 플래그 비트(UTF-8 플래그)를 확인하고, 잘못 디코딩된 CP437/Latin1 문자열을 CP949/UTF-8로 복원합니다.
    """
    # bit 11이 1이면 공식 UTF-8
    is_utf8_flag = bool(flag_bits & 0x800)
    
    if is_utf8_flag:
        return normalize_korean_text(filename)
    
    # UTF-8 플래그가 없는 경우 zipfile 모듈은 기본적으로 cp437로 디코딩함
    try:
        raw_bytes = filename.encode('cp437')
        return smart_decode_filename(raw_bytes)
    except Exception:
        try:
            raw_bytes = filename.encode('latin1')
            return smart_decode_filename(raw_bytes)
        except Exception:
            return normalize_korean_text(filename)

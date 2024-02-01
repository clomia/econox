""" 간단한 문자열 처리 도구들 """

import re


def strip(s: str):
    """스페이스, 개행 텝 등 공백 문자를 정리합니다."""
    return " ".join(re.split(r"\s+", s.strip()))

"""
기사에 사진이 없을 때, 헤드라인/제목에서 키워드를 뽑아 Pexels에서
관련 무료 스톡 이미지를 검색합니다.

Pexels는 상업적 이용을 포함해 무료로 쓸 수 있는 스톡 사진 API입니다.
(출처 표기 의무는 없지만, 해주면 좋습니다: https://www.pexels.com)

무료 API 키 발급: https://www.pexels.com/api/ 에서 가입 후 즉시 발급됩니다.
"""

import re
import requests

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"

# 뉴스 제목에서 자주 나오는 조사/어미 등을 제거해 검색 키워드 품질을 높이기 위한 간단한 필터
STOPWORDS = {"있다", "했다", "밝혔다", "위해", "대한", "관련", "이번", "지난", "오늘"}


def _extract_keyword(headline: str, title: str) -> str:
    """헤드라인/제목에서 검색에 쓸만한 명사 위주 키워드를 뽑아냅니다 (간단한 휴리스틱)."""
    text = f"{headline} {title}"
    # 한글/영문/숫자만 남기고 나머지는 공백 처리
    text = re.sub(r"[^\w\s가-힣]", " ", text)
    words = [w for w in text.split() if len(w) >= 2 and w not in STOPWORDS]
    # 가장 긴 단어 2~3개를 조합 (보통 고유명사/핵심어일 확률이 높음)
    words = sorted(set(words), key=len, reverse=True)[:2]
    return " ".join(words) if words else "news"


def search_related_photo(headline: str, title: str, pexels_api_key: str) -> "str | None":
    """
    관련 스톡 이미지 URL을 반환합니다. 실패하거나 결과가 없으면 None (사진 없이 진행).
    """
    if not pexels_api_key:
        return None

    keyword = _extract_keyword(headline, title)
    try:
        resp = requests.get(
            PEXELS_SEARCH_URL,
            headers={"Authorization": pexels_api_key},
            params={"query": keyword, "per_page": 1, "orientation": "square"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("photos", [])
        if not results:
            return None
        # large 사이즈 사용 (충분히 고화질)
        return results[0]["src"]["large"]
    except Exception as e:
        print(f"[경고] 관련 이미지 검색 실패, 사진 없이 진행합니다: {e}")
        return None

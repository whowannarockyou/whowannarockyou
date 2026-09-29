"""
Claude가 만들어준 영어 검색어(image_query)로 Pexels와 Unsplash 두 곳에서 관련 무료
스톡 이미지를 검색합니다. 다양성을 위해 매번 두 서비스 중 하나를 무작위로 먼저
시도하고, 결과가 없으면 다른 쪽을 시도합니다.

- Pexels: 출처 표기 의무 없음. https://www.pexels.com/api/ 에서 무료 API 키 발급.
- Unsplash: API로 사용 시 촬영자 + Unsplash 크레딧 표기가 필수입니다
  (Unsplash API 가이드라인: https://help.unsplash.com/en/articles/2511315).
  https://unsplash.com/oauth/applications 에서 앱 생성 후 Access Key 발급.

반환값은 {"url": 이미지URL, "attribution": 크레딧 문구 또는 None} 형태이며,
attribution이 있으면(Unsplash에서 왔으면) 캡션에 꼭 넣어줘야 합니다.
"""

import random
import requests

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"


def _search_pexels(image_query: str, pexels_api_key: str) -> "dict | None":
    if not pexels_api_key:
        return None
    try:
        resp = requests.get(
            PEXELS_SEARCH_URL,
            headers={"Authorization": pexels_api_key},
            params={"query": image_query, "per_page": 1, "orientation": "square"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("photos", [])
        if not results:
            return None
        return {"url": results[0]["src"]["large"], "attribution": None}
    except Exception as e:
        print(f"[경고] Pexels 검색 실패: {e}")
        return None


def _search_unsplash(image_query: str, unsplash_access_key: str) -> "dict | None":
    if not unsplash_access_key:
        return None
    try:
        resp = requests.get(
            UNSPLASH_SEARCH_URL,
            headers={"Authorization": f"Client-ID {unsplash_access_key}"},
            params={"query": image_query, "per_page": 1, "orientation": "squarish"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return None
        photo = results[0]
        photographer = photo["user"]["name"]
        attribution = f"사진: {photographer} (Unsplash)"
        return {"url": photo["urls"]["regular"], "attribution": attribution}
    except Exception as e:
        print(f"[경고] Unsplash 검색 실패: {e}")
        return None


def search_related_photo(image_query: str, pexels_api_key: str, unsplash_access_key: str = "") -> "dict | None":
    """
    image_query(영어 검색어)로 Pexels/Unsplash를 검색해 관련 스톡 이미지를 찾습니다.
    두 서비스 중 하나를 무작위로 먼저 시도하고, 실패하면 나머지를 시도합니다.
    반환값: {"url": ..., "attribution": ... 또는 None} / 둘 다 실패하면 None.
    """
    if not image_query:
        return None

    searchers = [
        ("pexels", lambda: _search_pexels(image_query, pexels_api_key)),
        ("unsplash", lambda: _search_unsplash(image_query, unsplash_access_key)),
    ]
    random.shuffle(searchers)

    for name, search_fn in searchers:
        result = search_fn()
        if result:
            print(f"  → {name}에서 이미지 찾음")
            return result

    return None

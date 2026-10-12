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


def _search_pexels(image_query: str, pexels_api_key: str, per_page: int = 8) -> list:
    """후보 사진 여러 장을 반환: [{"url","attribution","desc"}]"""
    if not pexels_api_key:
        return []
    try:
        resp = requests.get(
            PEXELS_SEARCH_URL,
            headers={"Authorization": pexels_api_key},
            params={"query": image_query, "per_page": per_page, "orientation": "square"},
            timeout=10,
        )
        resp.raise_for_status()
        return [
            {"url": p["src"]["large"], "attribution": None, "desc": p.get("alt") or ""}
            for p in resp.json().get("photos", [])
        ]
    except Exception as e:
        print(f"[경고] Pexels 검색 실패: {e}")
        return []


def _search_unsplash(image_query: str, unsplash_access_key: str, per_page: int = 8) -> list:
    if not unsplash_access_key:
        return []
    try:
        resp = requests.get(
            UNSPLASH_SEARCH_URL,
            headers={"Authorization": f"Client-ID {unsplash_access_key}"},
            params={"query": image_query, "per_page": per_page, "orientation": "squarish"},
            timeout=10,
        )
        resp.raise_for_status()
        out = []
        for photo in resp.json().get("results", []):
            out.append({
                "url": photo["urls"]["regular"],
                "attribution": f"사진: {photo['user']['name']} (Unsplash)",
                "desc": photo.get("alt_description") or photo.get("description") or "",
            })
        return out
    except Exception as e:
        print(f"[경고] Unsplash 검색 실패: {e}")
        return []


def _pick_best(candidates: list, headline: str, article_hint: str) -> "dict | None":
    """후보 사진 설명(alt 텍스트)을 보고 기사 주제에 가장 맞는 것 하나를 Claude가 고릅니다.
    어울리는 게 없으면 None. (사진 자체를 보는 게 아니라 설명 텍스트 기반 판단)"""
    try:
        import anthropic
        client = anthropic.Anthropic()
        listing = "\n".join(f"{i + 1}. {c['desc'] or '(설명 없음)'}" for i, c in enumerate(candidates))
        prompt = f"""인스타그램 카드뉴스 커버 배경으로 쓸 스톡 사진을 고르세요.

기사 헤드라인: {headline}
기사 주제 힌트: {article_hint}

후보 사진 설명(영어):
{listing}

기준:
- 기사 주제를 직관적으로 떠올리게 하는 구체적인 장면/사물이 담긴 사진을 고를 것
- 아무것도 없는 빈 공간, 추상적 배경, 무대/단상/건축 구조물만 있는 사진, 주제와 무관한 사진은 제외
- 특정 인물의 얼굴이 중심인 사진은 제외
- 어울리는 게 하나도 없으면 NONE

번호만 답하세요 (예: 3). 없으면 NONE."""
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        if "NONE" in text.upper():
            return None
        digits = "".join(ch for ch in text if ch.isdigit())
        idx = int(digits) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx]
    except Exception as e:
        print(f"[경고] 사진 선별 실패, 첫 후보를 사용합니다: {e}")
        return candidates[0] if candidates else None
    return None


def search_related_photo(
    image_query: str,
    pexels_api_key: str,
    unsplash_access_key: str = "",
    headline: str = "",
    alt_queries: "list[str] | None" = None,
    article_hint: str = "",
) -> "dict | None":
    """
    image_query(+대체 검색어)로 Pexels/Unsplash 후보를 모은 뒤, 기사 주제에 가장 맞는 사진 하나를 고릅니다.
    반환값: {"url": ..., "attribution": ... 또는 None} / 어울리는 사진이 없으면 None.
    """
    queries = [q for q in [image_query] + list(alt_queries or []) if q]
    if not queries:
        return None

    candidates, seen = [], set()
    for q in queries[:3]:
        batch = _search_pexels(q, pexels_api_key) + _search_unsplash(q, unsplash_access_key)
        random.shuffle(batch)
        for c in batch:
            if c["url"] not in seen:
                seen.add(c["url"])
                candidates.append(c)
        if len(candidates) >= 12:
            break

    if not candidates:
        return None
    candidates = candidates[:16]

    best = _pick_best(candidates, headline, article_hint) if headline else candidates[0]
    if best:
        print(f"  → 후보 {len(candidates)}장 중 기사에 맞는 사진 선택: {best['desc'][:50]}")
        return {"url": best["url"], "attribution": best["attribution"]}
    print("  → 기사에 어울리는 사진이 없어 사진 없이 진행합니다.")
    return None

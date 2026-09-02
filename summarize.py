"""
기사 본문/요약을 인스타그램 카드뉴스용 콘텐츠로 변환합니다.
Anthropic API(Claude)를 사용합니다. ANTHROPIC_API_KEY 환경변수가 필요합니다.

카드 2장(캐러셀) 구성:
- 1번 슬라이드(커버): headline + bullets (짧고 임팩트있게)
- 2번 슬라이드(상세): detail_points (조금 더 풀어서 설명)
"""

import os
import re
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def strip_html(text: str) -> str:
    """RSS summary에 섞여있는 HTML 태그 제거."""
    return re.sub(r"<[^>]+>", "", text).strip()


def summarize_for_card(title: str, raw_summary: str) -> dict:
    """
    기사 제목/요약을 받아서 캐러셀 2장짜리 카드뉴스 콘텐츠를 생성합니다.
    반환값: {
        "headline": str,           # 커버용 짧은 헤드라인 (줄바꿈은 호출부에서 처리)
        "bullets": [str, str, str] # 커버용 3개 핵심 포인트 (각 20자 내외)
        "detail_title": str,       # 상세 슬라이드 소제목
        "detail_points": [str x4]  # 상세 슬라이드용, 조금 더 풀어쓴 설명 4개 (각 40자 내외)
    }
    """
    clean_summary = strip_html(raw_summary)[:2000]

    prompt = f"""다음 뉴스를 인스타그램 카드뉴스(2장 캐러셀)용으로 가공해줘.

제목: {title}
내용: {clean_summary}

요구사항:
- headline: 14자 내외로 끊어 읽기 좋은 임팩트 있는 문구 (원제목을 그대로 베끼지 말 것)
- bullets: 핵심만 담은 3개의 아주 짧은 문장 (각 20자 이내)
- detail_title: 2번째 슬라이드용 소제목, "무엇이 달라지나요?" 같은 궁금증 유발형 (12자 내외)
- detail_points: 배경/맥락/영향 등을 조금 더 자세히 풀어쓴 4개 문장 (각 40자 이내, 존댓말)
- 반드시 아래 JSON 형식으로만 답해. 다른 설명 붙이지 마.

{{"headline": "...", "bullets": ["...", "...", "..."], "detail_title": "...", "detail_points": ["...", "...", "...", "..."]}}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 실패 시 안전한 fallback
        return {
            "headline": title[:20],
            "bullets": [clean_summary[:20], "", ""],
            "detail_title": "자세히 보기",
            "detail_points": [clean_summary[:40], "", "", ""],
        }


def build_caption(article_title: str, article_link: str, source_name: str) -> str:
    """게시물 본문(캡션)을 만듭니다. 저작권 보호를 위해 원문 링크와 출처를 명시합니다."""
    return (
        f"{article_title}\n\n"
        f"자세한 내용은 원문에서 확인하세요 🔗\n"
        f"출처: {source_name}\n"
        f"(전문 보기는 프로필 링크 또는 아래 URL)\n"
        f"{article_link}\n\n"
        f"#뉴스 #{source_name.replace(' ', '')} #오늘의뉴스"
    )

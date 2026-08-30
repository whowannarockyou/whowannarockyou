"""
기사 본문/요약을 인스타그램 카드뉴스용 짧은 문구로 변환합니다.
Anthropic API(Claude)를 사용합니다. ANTHROPIC_API_KEY 환경변수가 필요합니다.
"""

import os
import re
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def strip_html(text: str) -> str:
    """RSS summary에 섞여있는 HTML 태그 제거."""
    return re.sub(r"<[^>]+>", "", text).strip()


def summarize_for_card(title: str, raw_summary: str) -> dict:
    """
    기사 제목/요약을 받아서 카드뉴스용 헤드라인 + 3줄 요약을 생성합니다.
    반환값: {"headline": str, "bullets": [str, str, str]}
    """
    clean_summary = strip_html(raw_summary)[:1500]

    prompt = f"""다음 뉴스를 인스타그램 카드뉴스용으로 요약해줘.

제목: {title}
내용: {clean_summary}

요구사항:
- headline: 12자 내외의 임팩트 있는 한 줄 (원제목을 그대로 베끼지 말고 다르게 표현)
- bullets: 핵심 내용을 담은 3개의 짧은 문장 (각 25자 이내)
- 반드시 아래 JSON 형식으로만 답해. 다른 설명 붙이지 마.

{{"headline": "...", "bullets": ["...", "...", "..."]}}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    import json
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 실패 시 안전한 fallback
        return {
            "headline": title[:20],
            "bullets": [clean_summary[:25], "", ""],
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

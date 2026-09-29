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
- headline: 스크롤을 멈추게 할 만큼 강렬한 후킹 문구. 아래 두 방식 중 기사 내용에 더 잘 맞는 쪽으로 작성:
  (a) 강한 키워드형 - 임팩트 있는 단어를 앞세운 단정적 문장 ("결국 터졌다", "역대 최대 규모" 같은 톤)
  (b) 질문형 - 궁금증을 유발하는 물음표 문장 ("이게 가능하다고?", "왜 지금 이걸 발표했을까?" 같은 톤)
  14자 내외로 짧게, 원제목을 그대로 베끼지 말 것. 과장은 하되 기사에 없는 사실을 지어내거나 왜곡하지는 말 것 (낚시성 거짓 정보 금지, 어디까지나 사실 기반의 강조).
- bullets: 핵심만 담은 3개의 아주 짧은 문장 (각 20자 이내)
- detail_title: 2번째 슬라이드용 소제목, "무엇이 달라지나요?" 같은 궁금증 유발형 (12자 내외)
- detail_points: 배경/맥락/영향 등을 조금 더 자세히 풀어쓴 4개 문장 (각 40자 이내, 존댓말)
- image_query: 커버 사진을 검색할 때 쓸 영어 키워드 2~4단어. 기사의 구체적인 고유명사(인명·지명·연도)나
  사건명이 아니라, 그 기사가 풍기는 "장면/분위기"를 묘사하는 일반적인 영어 단어로 작성할 것
  (예: 전쟁 관련 기사 → "war destruction city", 예산 기사 → "government budget meeting",
  귀성길 기사 → "train station travel crowd"). 스톡사진 검색엔진에 넣을 검색어이므로
  실존 인물/사건 이름이 아니라 시각적으로 존재할 법한 장면 위주로 작성.
- tag: 커버 이미지 상단 태그에 넣을 한 단어. 아래 목록 중 기사 톤에 가장 잘 맞는 것 하나를 고를 것
  (반드시 이 목록 안에서만 선택): "논란", "단독", "충격", "속보", "화제", "이거 실화", "주목"
  - 의혹/비판/논쟁성 기사 → "논란"
  - 특종성, 처음 알려지는 사실 → "단독"
  - 놀랍거나 충격적인 사실 폭로 → "충격"
  - 막 발생한 긴급 뉴스 → "속보"
  - 이미 화제가 되고 있는 이슈 → "화제"
  - 황당하거나 비상식적인 상황 → "이거 실화"
  - 위 어디에도 뚜렷하게 안 맞으면 → "주목"
- is_person_focused: 이 기사가 **특정 실존 인물(정치인·연예인·기업인 등 공인) 개인이 중심**인 기사인지
  true/false로 판단. 정책/사건/지역 이슈처럼 특정 인물의 얼굴이 핵심이 아닌 기사는 false.
  (예: "○○ 의원, 막말 논란" → true / "정부 예산안 발표" → false)
- outlook: "앞으로의 전망" 2~3문장 (존댓말). 반드시 기사에 실제로 언급된 다음 절차/일정/조건
  (예: "국회 심의를 거쳐야 한다", "다음 달 결과가 발표될 예정이다" 등)에 근거해서만 작성할 것.
  기사에 없는 내용을 추측해서 단정적으로 말하지 말고, "~할 전망입니다", "~할 것으로 보입니다",
  "~여부가 주목됩니다" 처럼 조심스러운 표현을 쓸 것. 기사에 향후 일정/절차 언급이 전혀 없으면
  빈 문자열("")로 둘 것 (억지로 지어내지 말 것).
- 반드시 아래 JSON 형식으로만 답해. 다른 설명 붙이지 마.

{{"headline": "...", "bullets": ["...", "...", "..."], "detail_title": "...", "detail_points": ["...", "...", "...", "..."], "image_query": "...", "tag": "...", "is_person_focused": false, "outlook": "..."}}
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
            "image_query": "news paper background",
            "tag": "주목",
            "is_person_focused": False,
            "outlook": "",
        }


def build_caption(
    article_title: str,
    article_link: str,
    source_name: str,
    bullets: "list[str] | None" = None,
    detail_points: "list[str] | None" = None,
    outlook: str = "",
) -> str:
    """게시물 본문(캡션)을 만듭니다. 기사 제목 + 핵심 요약 + 상세 설명 + 앞으로의 전망 + 출처/링크."""
    lines = [article_title, ""]

    for b in (bullets or []):
        if b:
            lines.append(f"· {b}")
    if bullets:
        lines.append("")

    for p in (detail_points or []):
        if p:
            lines.append(p)
    if detail_points:
        lines.append("")

    if outlook:
        lines.append(f"🔮 앞으로는? {outlook}")
        lines.append("")

    lines.append(f"📷 {source_name} | {article_link}")
    return "\n".join(lines)


def pick_hottest_article(candidates: list) -> int:
    """
    여러 후보 기사(title, summary 속성을 가진 객체 리스트) 중
    인스타그램에서 가장 화제가 될 만한 기사를 Claude가 골라 인덱스를 반환합니다.
    ※ 실제 조회수/실시간 인기 데이터가 아니라 Claude가 제목/요약만 보고 추정하는 것입니다.
    실패 시 0번(가장 최신 기사)을 반환합니다.
    """
    if len(candidates) <= 1:
        return 0

    listing = "\n".join(
        f"{i + 1}. {a.title} - {strip_html(a.summary)[:100]}"
        for i, a in enumerate(candidates)
    )
    prompt = f"""다음은 오늘의 최신 뉴스 후보 목록입니다.

{listing}

이 중 인스타그램에서 가장 화제가 되고 반응이 좋을 만한 기사 하나를 고르세요.
판단 기준: 대중적 관심도, 논쟁성/화제성, 시의성, 감정적 임팩트.
다른 설명 없이 번호만 답하세요 (예: 3)."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        digits = "".join(ch for ch in text if ch.isdigit())
        idx = int(digits) - 1
        if 0 <= idx < len(candidates):
            return idx
    except Exception as e:
        print(f"[경고] 화제성 판단 실패, 최신 기사로 진행합니다: {e}")

    return 0

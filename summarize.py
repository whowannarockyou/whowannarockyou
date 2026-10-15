"""
기사 본문/요약을 인스타그램 카드뉴스용 콘텐츠로 변환합니다.
Anthropic API(Claude)를 사용합니다. ANTHROPIC_API_KEY 환경변수가 필요합니다.

카드 4장(캐러셀) 구성 (커버/상세/앞으로의 방향/클로징):
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
- headline: 스크롤을 멈추게 할 확실한 후킹 문구. 아래 세 방식 중 기사 내용과 분위기에 가장 잘 맞는 쪽으로 작성:
  (a) 강한 키워드형 - 임팩트 있는 단어를 앞세운 단정적 문장 ("결국 터졌다", "역대 최대 규모" 같은 톤)
  (b) 질문형 - 궁금증을 유발하는 물음표 문장 ("이게 가능하다고?", "왜 지금 이걸 발표했을까?" 같은 톤)
  (c) 유머/위트형 - 재치 있는 말장난, 과장된 비유, 공감 가는 한마디 ("월급 빼고 다 올랐다", "이 정도면 날씨가 개인 감정 있는 듯" 같은 톤).
      가볍거나 일상적인 소재(물가, 날씨, 트렌드, 생활, 문화, 스포츠 결과 등)에만 사용할 것.
  ※ 사망·사고·재난·범죄 피해·질병·전쟁 등 무겁거나 피해자가 있는 소재, 그리고 특정 실존 인물을 조롱하거나 비하하는 소재에는
    유머를 절대 쓰지 말고 (a) 또는 (b)로 진지하게 작성할 것.
  14자 내외로 짧게, 원제목을 그대로 베끼지 말 것. 과장은 하되 기사에 없는 사실을 지어내거나 왜곡하지는 말 것
  (낚시성 거짓 정보 금지, 어디까지나 사실 기반의 강조와 재치).
- bullets: 핵심만 담은 3개의 아주 짧은 문장 (각 20자 이내)
- detail_title: 2번째 슬라이드용 소제목, "무엇이 달라지나요?" 같은 궁금증 유발형 (12자 내외)
- detail_points: 배경/맥락/영향 등을 조금 더 자세히 풀어쓴 4개 문장 (각 40자 이내, 존댓말)
- image_query: 커버 사진을 검색할 때 쓸 영어 키워드 2~4단어. 기사 주제를 **직관적으로 떠올리게 하는 구체적인 사물/장면**을
  묘사할 것 (예: 노벨경제학상 → "nobel prize medal", 금리 → "bank interest rate calculator",
  귀성길 → "train station travel crowd", 반도체 → "semiconductor chip closeup", 전쟁 → "war destruction city").
  사람 이름·고유명사는 쓰지 말고, "podium", "stage", "empty room", "minimal", "background", "abstract",
  "architecture" 처럼 주제와 상관없이 아무 기사에나 어울리는 모호한 단어는 쓰지 말 것.
- image_queries_alt: 위와 다른 각도의 대체 영어 검색어 2개 (각 2~4단어, 같은 원칙). 첫 검색어로 좋은 사진이 없을 때 사용.
- tag: 커버 이미지 상단 태그에 넣을 한 단어. 아래 목록 중 기사 톤에 가장 잘 맞는 것 하나를 고를 것
  (반드시 이 목록 안에서만 선택): "논란", "단독", "충격", "속보", "화제", "이거 실화", "주목"
  - 의혹/비판/논쟁성 기사 → "논란"
  - 특종성, 처음 알려지는 사실 → "단독"
  - 놀랍거나 충격적인 사실 폭로 → "충격"
  - 막 발생한 긴급 뉴스 → "속보"
  - 이미 화제가 되고 있는 이슈 → "화제"
  - 황당하거나 비상식적인 상황 → "이거 실화"
  - 위 어디에도 뚜렷하게 안 맞으면 → "주목"
- is_person_focused: 이 기사가 **특정 실존 인물(정치인·연예인·기업인·운동선수·감독 등 공인) 개인이 중심**인 기사인지
  true/false로 판단. 정책/사건/지역 이슈처럼 특정 인물의 얼굴이 핵심이 아닌 기사는 false.
  아래 신호 중 하나라도 있으면 true로 판단할 것:
  - 헤드라인/제목에 특정 인물의 이름이 명시되어 있음
  - 헤드라인/제목에 그 인물의 **직접 인용문("...")**이 포함됨 (예: "제 책임" 이라고 밝혔다)
  - 스포츠 감독·선수 개인의 발언/거취/활약이 핵심인 기사
  (예: "○○ 의원, 막말 논란" → true / "정부 예산안 발표" → false /
   "[아시안게임] ○○ 감독 \"제 책임\"" → true)
- outlook: "앞으로의 전망" 2~3문장 (존댓말). 반드시 기사에 실제로 언급된 다음 절차/일정/조건
  (예: "국회 심의를 거쳐야 한다", "다음 달 결과가 발표될 예정이다" 등)에 근거해서만 작성할 것.
  기사에 없는 내용을 추측해서 단정적으로 말하지 말고, "~할 전망입니다", "~할 것으로 보입니다",
  "~여부가 주목됩니다" 처럼 조심스러운 표현을 쓸 것. 기사에 향후 일정/절차 언급이 전혀 없으면
  빈 문자열("")로 둘 것 (억지로 지어내지 말 것).
- direction_title / direction_points: 3번째 슬라이드("앞으로 지켜볼 점")는 **꼭 필요한 기사에만** 만든다.
  만드는 경우: 경제·금융·부동산·증시·물가·금리·산업/기업 실적·정책/법안·제도 변경처럼
  독자가 앞으로의 일정이나 변화에 대비하거나 지켜볼 만한 기사.
  만들지 않는 경우(direction_title은 "", direction_points는 빈 리스트 []):
  사건사고, 날씨, 스포츠 경기 결과, 연예/문화, 인물 소식, 단순 발표·행사 소식, 그 밖에 앞으로 지켜볼 사항이 뚜렷하지 않은 기사.
  만들 때는: direction_title은 "이제 무엇을 지켜봐야 할까요?" 같은 톤(14자 내외),
  direction_points는 앞으로 지켜볼 핵심 포인트나 대응 방향 3개 (각 40자 이내, 존댓말).
  반드시 기사 내용(쟁점, 절차, 일정, 이해관계)에서 논리적으로 이어지는 것만 쓰고, 기사에 없는 사실이나 수치를 지어내지 말 것.
  단정 대신 "~이 관건입니다", "~여부를 지켜봐야 합니다", "~할 필요가 있습니다" 같은 표현을 쓸 것.
  개인(실존 인물)을 비난·비하하는 표현 금지. 애매하면 만들지 말고 빈 리스트로 둘 것.
- caption: 인스타그램 게시물 본문(캡션). 딱딱한 기사 요약이 아니라 **친구에게 말해주듯 자연스러운 글**로 쓸 것.
  - 첫 줄: 스크롤 멈추게 하는 훅 한 줄 (질문이나 한마디). 기사 제목이나 headline을 그대로 복사하지 말 것. 이모지 가능.
  - 이어서 짧은 문단 3~4개 (각 1~2문장, 문단 사이 빈 줄). "~해요", "~했어요", "~거든요" 같은 부드러운 해요체.
    "~했습니다", "~것으로 알려졌습니다" 같은 보도체와 개조식(· 불릿)은 쓰지 말 것.
    어려운 용어는 쉬운 말로 풀어 쓰고, 왜 중요한지 한 번은 짚어줄 것.
  - 기사에 있는 사실만 쓸 것. 수치·이름·기관명은 정확히, 없는 내용을 지어내거나 추측해서 단정하지 말 것.
  - outlook이 있으면 마지막 문단에 자연스럽게 녹일 것 ("앞으로는 ~ 지켜봐야 해요" 식).
  - 마지막 줄: 독자에게 가볍게 던지는 질문 한 줄 (댓글 유도). 정치·사건 기사에서는 특정 정당/인물 편을 들게 하는 질문 금지
    ("여러분은 어떻게 보세요?" 수준으로).
  - 사망·사고·재난·피해자가 있는 기사, 연예인 사생활·의혹 기사는 이모지 없이 차분한 톤으로.
  - 전체 400자 안팎, 이모지는 3개 이하. 해시태그·링크·출처 표기는 넣지 말 것 (출처는 코드가 따로 붙임).
- 연예/문화 기사 주의사항: 연예인·방송·콘텐츠 기사는 반드시 기사에 확인된 사실만 쓸 것.
  열애·결혼·이혼·사생활·루머·의혹·소송·사건사고 관련 내용은 추측이나 단정 없이 기사에 나온 표현 수준으로만 전하고,
  유머/조롱 톤은 쓰지 말 것. 사망·질병 소식은 애도하는 차분한 톤으로 쓸 것.
  작품·공연·앨범·방송 소식처럼 밝은 소재는 유머형 후킹도 가능. 연예/문화 기사는 direction_points를 빈 리스트([])로 둘 것.
- 반드시 아래 JSON 형식으로만 답해. 다른 설명 붙이지 마.

{{"headline": "...", "caption": "...", "bullets": ["...", "...", "..."], "detail_title": "...", "detail_points": ["...", "...", "...", "..."], "image_query": "...", "image_queries_alt": ["...", "..."], "tag": "...", "is_person_focused": false, "outlook": "...", "direction_title": "...", "direction_points": ["...", "...", "..."]}}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2200,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 실패 시 안전한 fallback
        print(f"[경고] Claude 응답을 JSON으로 읽지 못해 기본값으로 대체합니다 (응답 길이 {len(text)}자). "
              f"응답이 중간에 잘렸을 수 있습니다. 응답 끝부분: ...{text[-80:]}")
        return {
            "headline": title[:20],
            "caption": "",
            "bullets": [clean_summary[:20], "", ""],
            "detail_title": "자세히 보기",
            "detail_points": [clean_summary[:40], "", "", ""],
            "image_query": "news paper background",
            "image_queries_alt": [],
            "tag": "주목",
            "is_person_focused": False,
            "outlook": "",
            "direction_title": "",
            "direction_points": [],
        }


def build_caption(
    article_title: str,
    article_link: str,
    source_name: str,
    bullets: "list[str] | None" = None,
    detail_points: "list[str] | None" = None,
    outlook: str = "",
    caption_body: str = "",
) -> str:
    """게시물 본문(캡션)을 만듭니다. 기사 제목 + 핵심 요약 + 상세 설명 + 앞으로의 전망 + 출처/링크."""
    if caption_body:
        # Claude가 쓴 자연스러운 본문이 있으면 그대로 쓰고 출처만 붙임
        return f"{caption_body.strip()}\n\n📷 {source_name}"

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

    lines.append(f"📷 {source_name}")
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

"""
헤드라인 + 요약 불릿을 받아 인스타그램용 1080x1080 카드뉴스 이미지를 생성합니다.
"""

import textwrap
from PIL import Image, ImageDraw, ImageFont

CARD_SIZE = (1080, 1080)
BG_COLOR = (17, 24, 39)       # 다크 네이비
ACCENT_COLOR = (250, 204, 21)  # 포인트 옐로우
TEXT_COLOR = (255, 255, 255)
SUB_COLOR = (209, 213, 219)

# 폰트 경로: 시스템에 있는 한글 지원 폰트로 교체하세요.
# 예) 나눔고딕: /usr/share/fonts/truetype/nanum/NanumGothicBold.ttf
FONT_BOLD = "fonts/NanumGothicBold.ttf"
FONT_REGULAR = "fonts/NanumGothic.ttf"


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        # 폰트 파일이 없으면 기본 폰트로 대체 (한글 깨질 수 있음 - 반드시 폰트 준비 권장)
        return ImageFont.load_default()


def generate_card(headline: str, bullets: list[str], source_name: str, output_path: str) -> str:
    img = Image.new("RGB", CARD_SIZE, BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_headline = _load_font(FONT_BOLD, 72)
    font_bullet = _load_font(FONT_REGULAR, 40)
    font_source = _load_font(FONT_REGULAR, 32)

    # 상단 포인트 바
    draw.rectangle([(0, 0), (CARD_SIZE[0], 16)], fill=ACCENT_COLOR)

    # 헤드라인 (줄바꿈 처리)
    wrapped_headline = textwrap.wrap(headline, width=12)
    y = 220
    for line in wrapped_headline:
        draw.text((80, y), line, font=font_headline, fill=TEXT_COLOR)
        y += 90

    # 구분선
    y += 40
    draw.line([(80, y), (1000, y)], fill=ACCENT_COLOR, width=4)
    y += 60

    # 불릿 포인트
    for bullet in bullets:
        if not bullet:
            continue
        wrapped = textwrap.wrap(bullet, width=22)
        for line in wrapped:
            draw.text((100, y), f"· {line}", font=font_bullet, fill=SUB_COLOR)
            y += 56
        y += 20

    # 하단 출처 표기
    draw.text((80, CARD_SIZE[1] - 100), f"출처: {source_name}", font=font_source, fill=SUB_COLOR)

    img.save(output_path, quality=95)
    return output_path

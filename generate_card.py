"""
캐러셀(2장) 카드뉴스 이미지를 생성합니다.
- generate_cover_card(): 1번 슬라이드 - 기사 사진 + 헤드라인 + 핵심 불릿
- generate_detail_card(): 2번 슬라이드 - 소제목 + 번호 매긴 상세 설명

디자인 톤: 다크 배경 + 볼드 화이트 타이포 + 포인트 컬러 (토스 스타일 참고)
"""

import io
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont

CARD_SIZE = (1080, 1080)
BG_TOP = (13, 13, 18)
BG_BOTTOM = (6, 6, 9)
ACCENT = (124, 58, 237)       # 포인트 컬러 (보라). 브랜드에 맞게 바꿔도 됨
TEXT_MAIN = (255, 255, 255)
TEXT_SUB = (198, 201, 209)
TEXT_MUTED = (140, 142, 150)

# 폰트 경로: fonts/ 폴더에 나눔고딕 계열을 넣어서 사용합니다.
FONT_BOLD = "fonts/NanumGothicExtraBold.ttf"   # 없으면 NanumGothicBold.ttf로 대체 가능
FONT_REGULAR = "fonts/NanumGothic.ttf"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        try:
            # ExtraBold가 없으면 Bold로 대체
            return ImageFont.truetype("fonts/NanumGothicBold.ttf", size)
        except OSError:
            return ImageFont.load_default()


def _dark_gradient_bg() -> Image.Image:
    img = Image.new("RGB", CARD_SIZE, BG_TOP)
    draw = ImageDraw.Draw(img)
    W, H = CARD_SIZE
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return img


def _draw_pill_tag(draw: ImageDraw.ImageDraw, text: str, xy: tuple, font: ImageFont.FreeTypeFont):
    x, y = xy
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    pad_x, pad_y = 26, 12
    draw.rounded_rectangle([x, y, x + w + pad_x * 2, y + h + pad_y * 2], radius=28, fill=ACCENT)
    draw.text((x + pad_x, y + pad_y - 3), text, font=font, fill=TEXT_MAIN)


def _draw_page_dots(draw: ImageDraw.ImageDraw, active_index: int, total: int = 2):
    W, H = CARD_SIZE
    dot_w, gap = 16, 14
    total_w = total * dot_w + (total - 1) * gap
    start_x = (W - total_w) / 2
    y = H - 80
    for i in range(total):
        x = start_x + i * (dot_w + gap)
        if i == active_index:
            draw.ellipse([x, y, x + dot_w, y + dot_w * 0.5 + 8], fill=ACCENT)
        else:
            draw.ellipse([x, y, x + dot_w, y + dot_w * 0.5 + 8], outline=(120, 120, 130), width=2)


def _download_image(url: str) -> "Image.Image | None":
    """기사 이미지 URL을 다운로드합니다. 실패하면 None을 반환 (사진 없이 진행)."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    except Exception as e:
        print(f"[경고] 기사 이미지 다운로드 실패, 사진 없이 진행합니다: {e}")
        return None


def _center_crop_resize(photo: Image.Image, target_w: int, target_h: int) -> Image.Image:
    target_ratio = target_w / target_h
    src_ratio = photo.width / photo.height
    if src_ratio > target_ratio:
        new_w = int(photo.height * target_ratio)
        left = (photo.width - new_w) // 2
        photo = photo.crop((left, 0, left + new_w, photo.height))
    else:
        new_h = int(photo.width / target_ratio)
        top = (photo.height - new_h) // 2
        photo = photo.crop((0, top, photo.width, top + new_h))
    return photo.resize((target_w, target_h))


def generate_cover_card(
    headline: str,
    bullets: list[str],
    source_name: str,
    image_url: str,
    output_path: str,
    tag_text: str = "오늘의 뉴스",
) -> str:
    """1번 슬라이드: 기사 사진(있으면) + 헤드라인 + 핵심 불릿."""
    W, H = CARD_SIZE
    img = _dark_gradient_bg()

    font_headline = _font(FONT_BOLD, 68)
    font_bullet = _font(FONT_REGULAR, 34)
    font_tag = _font(FONT_BOLD, 26)
    font_source = _font(FONT_REGULAR, 28)

    photo = _download_image(image_url)
    photo_h = 0
    if photo is not None:
        photo_h = 620
        photo = _center_crop_resize(photo, W, photo_h)
        img.paste(photo, (0, 0))

        # 사진 하단을 배경색으로 자연스럽게 페이드아웃
        fade_h = 220
        fade_mask = Image.new("L", (W, fade_h), 0)
        fmask_draw = ImageDraw.Draw(fade_mask)
        for y in range(fade_h):
            fmask_draw.line([(0, y), (W, y)], fill=int(255 * (y / fade_h)))
        dark_block = Image.new("RGB", (W, fade_h), BG_TOP)
        img.paste(dark_block, (0, photo_h - fade_h), fade_mask)

    draw = ImageDraw.Draw(img)

    tag_y = 60 if photo_h else 90
    _draw_pill_tag(draw, tag_text, (60, tag_y), font_tag)

    # 헤드라인 (사진 있으면 사진 아래, 없으면 중상단부터)
    y = (photo_h - 40) if photo_h else 260
    wrapped_headline = textwrap.wrap(headline, width=10)
    for line in wrapped_headline:
        draw.text((60, y), line, font=font_headline, fill=TEXT_MAIN)
        y += 88

    y += 30
    for b in bullets:
        if not b:
            continue
        draw.ellipse([60, y + 12, 68, y + 20], fill=ACCENT)
        wrapped_b = textwrap.wrap(b, width=22)
        for line in wrapped_b:
            draw.text((84, y), line, font=font_bullet, fill=TEXT_SUB)
            y += 46
        y += 10

    draw.text((60, H - 70), f"출처: {source_name}", font=font_source, fill=TEXT_MUTED)
    _draw_page_dots(draw, active_index=0)

    img.save(output_path, quality=95)
    return output_path


def generate_detail_card(
    detail_title: str,
    detail_points: list[str],
    output_path: str,
    tag_text: str = "자세히 보기",
) -> str:
    """2번 슬라이드: 소제목 + 번호 매긴 상세 설명 4개."""
    W, H = CARD_SIZE
    img = _dark_gradient_bg()
    draw = ImageDraw.Draw(img)

    font_title = _font(FONT_BOLD, 52)
    font_body = _font(FONT_REGULAR, 34)
    font_num = _font(FONT_BOLD, 32)
    font_tag = _font(FONT_BOLD, 26)

    _draw_pill_tag(draw, tag_text, (80, 90), font_tag)

    y = 190
    draw.text((80, y), detail_title, font=font_title, fill=TEXT_MAIN)
    y += 100

    for i, point in enumerate([p for p in detail_points if p], 1):
        circle_r = 20
        draw.ellipse([80, y, 80 + circle_r * 2, y + circle_r * 2], outline=ACCENT, width=3)
        num_bbox = draw.textbbox((0, 0), str(i), font=font_num)
        nw = num_bbox[2] - num_bbox[0]
        draw.text((80 + circle_r - nw / 2, y + circle_r - 22), str(i), font=font_num, fill=ACCENT)

        wrapped = textwrap.wrap(point, width=22)
        ty = y - 2
        for line in wrapped:
            draw.text((140, ty), line, font=font_body, fill=TEXT_SUB)
            ty += 46
        y = max(ty, y + circle_r * 2 + 10) + 30

    _draw_page_dots(draw, active_index=1)

    img.save(output_path, quality=95)
    return output_path

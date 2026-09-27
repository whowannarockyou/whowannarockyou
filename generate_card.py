"""
캐러셀(2장) 카드뉴스 이미지를 생성합니다.
- generate_cover_card(): 1번 슬라이드 - 기사 사진 전체 배경 + 아웃라인 태그 + 헤드라인 + 서브바
- generate_detail_card(): 2번 슬라이드 - 소제목 + 번호 매긴 상세 설명

디자인: 사진이 있으면 전체 배경으로 꽉 채우고 하단에 다크 그라데이션을 깔아 텍스트 가독성을 확보합니다.
사진이 없으면 같은 레이아웃을 다크 그라데이션 배경만으로 대체합니다.
"""

import io
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont

CARD_SIZE = (1080, 1080)
BG_TOP = (20, 21, 26)
BG_BOTTOM = (6, 6, 9)
ACCENT = (124, 58, 237)       # 포인트 컬러 (보라). 브랜드에 맞게 바꿔도 됨
TEXT_MAIN = (255, 255, 255)
TEXT_SUB = (230, 230, 232)
TEXT_MUTED = (150, 150, 156)
TEXT_FAINT = (110, 110, 118)  # 출처 등 최소화된 표기용 (아주 옅은 회색)

MARGIN = 150  # 좌우 안전 여백 (인스타 그리드 크롭 대비, 전체 폭의 약 14%)

# 폰트 경로: fonts/ 폴더에 나눔고딕 계열을 넣어서 사용합니다.
FONT_BOLD = "fonts/NanumGothicExtraBold.ttf"   # 없으면 NanumGothicBold.ttf로 대체
FONT_REGULAR = "fonts/NanumGothic.ttf"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        try:
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


def _outline_pill(draw: ImageDraw.ImageDraw, text: str, xy: tuple, font: ImageFont.FreeTypeFont) -> int:
    """흰색 테두리만 있는 투명 pill 태그. 반환값: 다음 태그를 이어붙일 x 끝 좌표."""
    x, y = xy
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 22, 12
    x2, y2 = x + w + pad_x * 2, y + h + pad_y * 2
    draw.rounded_rectangle([x, y, x2, y2], radius=(y2 - y) // 2, outline=TEXT_MAIN, width=2)
    draw.text((x + pad_x, y + pad_y - 2), text, font=font, fill=TEXT_MAIN)
    return x2


def _download_image(url: str) -> "Image.Image | None":
    """기사/스톡 이미지 URL을 다운로드합니다. 실패하면 None (사진 없이 진행)."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    except Exception as e:
        print(f"[경고] 이미지 다운로드 실패, 사진 없이 진행합니다: {e}")
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
    # LANCZOS: 축소/확대 모두에서 가장 선명한 결과를 주는 고품질 리샘플링 필터
    return photo.resize((target_w, target_h), Image.LANCZOS)


def generate_cover_card(
    headline: str,
    bullets: list[str],
    source_name: str,
    image_url: str,
    output_path: str,
    instagram_handle: str = "",
    tags: "list[str] | None" = None,
) -> str:
    """
    1번 슬라이드: 사진(있으면 전체 배경) + 아웃라인 태그 + 헤드라인 + 서브바.
    하단 중앙엔 본인 인스타그램 핸들(@instagram_handle)을 표시하고,
    출처는 우측 하단에 아주 작은 글씨로 최소화해서 표기합니다.
    """
    W, H = CARD_SIZE
    photo = _download_image(image_url)

    if photo is not None:
        img = _center_crop_resize(photo, W, H)
        # 하단부에 다크 그라데이션 오버레이 (사진 전체 위에, 텍스트 가독성 확보)
        overlay_h = 620
        overlay = Image.new("L", (W, overlay_h), 0)
        odraw = ImageDraw.Draw(overlay)
        for y in range(overlay_h):
            odraw.line([(0, y), (W, y)], fill=int(235 * (y / overlay_h)))
        dark_layer = Image.new("RGB", (W, overlay_h), (5, 5, 8))
        img.paste(dark_layer, (0, H - overlay_h), overlay)
    else:
        img = _dark_gradient_bg()

    draw = ImageDraw.Draw(img)

    font_tag = _font(FONT_BOLD, 26)
    font_headline = _font(FONT_BOLD, 60)
    font_sub = _font(FONT_REGULAR, 27)
    font_handle = _font(FONT_REGULAR, 24)
    font_source = _font(FONT_REGULAR, 18)

    # 콘텐츠 시작 y좌표: 사진 있으면 하단 정렬, 없으면 중앙보다 살짝 아래
    content_start_y = (H - 480) if photo is not None else 460

    # 아웃라인 태그들
    y_tag = content_start_y
    x_cursor = MARGIN
    for tag in (tags or ["오늘의 뉴스"]):
        x_cursor = _outline_pill(draw, tag, (x_cursor, y_tag), font_tag) + 16

    # 헤드라인 (최대 2줄)
    y = y_tag + 80
    wrapped_headline = textwrap.wrap(headline, width=10)[:2]
    for line in wrapped_headline:
        draw.text((MARGIN, y), line, font=font_headline, fill=TEXT_MAIN)
        y += 76

    # 서브 바 (다크 바 + 구분선 + 핵심 불릿 첫 줄)
    bar_y = y + 36
    bar_h = 60
    draw.rectangle([0, bar_y, W, bar_y + bar_h], fill=(8, 8, 10))
    draw.line([(MARGIN, bar_y + 14), (MARGIN, bar_y + bar_h - 14)], fill=ACCENT, width=3)
    sub_text = bullets[0] if bullets else ""
    draw.text((MARGIN + 22, bar_y + 15), sub_text, font=font_sub, fill=TEXT_SUB)

    # 하단: 중앙엔 본인 인스타 핸들, 우측 아래엔 아주 작은 출처 표기 (최소화)
    if instagram_handle:
        handle_text = f"@{instagram_handle}"
        hbbox = draw.textbbox((0, 0), handle_text, font=font_handle)
        hw = hbbox[2] - hbbox[0]
        draw.text(((W - hw) / 2, H - 66), handle_text, font=font_handle, fill=TEXT_MUTED)

    source_text = f"ⓒ{source_name}"
    sbbox = draw.textbbox((0, 0), source_text, font=font_source)
    sw = sbbox[2] - sbbox[0]
    draw.text((W - MARGIN - sw + 60, H - 34), source_text, font=font_source, fill=TEXT_FAINT)

    img.save(output_path, format="JPEG", quality=100, subsampling=0, optimize=True)
    return output_path


def generate_closing_card(
    brand_name: str,
    tagline: str,
    output_path: str,
    instagram_handle: str = "",
    button_text: str = "팔로우",
) -> str:
    """
    3번째 슬라이드(클로징): 상하단 레터박스 바 + 중앙 브랜드 워드마크
    + 팔로우 버튼(아웃라인) + 태그라인. 다크 배경 위주의 심플한 CTA 화면.
    """
    W, H = CARD_SIZE
    img = _dark_gradient_bg()
    draw = ImageDraw.Draw(img)

    # 상하단 레터박스 바 (시네마틱한 느낌의 프레이밍)
    bar_h = 46
    draw.rectangle([0, 0, W, bar_h], fill=(0, 0, 0))
    draw.rectangle([0, H - bar_h, W, H], fill=(0, 0, 0))

    font_logo = _font(FONT_BOLD, 96)
    font_btn = _font(FONT_BOLD, 32)
    font_tagline = _font(FONT_REGULAR, 34)
    font_handle = _font(FONT_REGULAR, 22)

    # 중앙 브랜드 워드마크
    lb = draw.textbbox((0, 0), brand_name, font=font_logo)
    lw, lh = lb[2] - lb[0], lb[3] - lb[1]
    logo_y = H * 0.42
    draw.text(((W - lw) / 2, logo_y), brand_name, font=font_logo, fill=TEXT_MAIN)

    # 팔로우 버튼 (아웃라인 pill)
    bb = draw.textbbox((0, 0), button_text, font=font_btn)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    pad_x, pad_y = 56, 20
    btn_w, btn_h = bw + pad_x * 2, bh + pad_y * 2
    btn_x = (W - btn_w) / 2
    btn_y = logo_y + lh + 64
    draw.rounded_rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h], radius=btn_h // 2, outline=TEXT_MAIN, width=3)
    draw.text((btn_x + pad_x, btn_y + pad_y - 3), button_text, font=font_btn, fill=TEXT_MAIN)

    # 태그라인 (중앙 정렬, 최대 2줄)
    y = btn_y + btn_h + 46
    for line in textwrap.wrap(tagline, width=15)[:2]:
        tb = draw.textbbox((0, 0), line, font=font_tagline)
        tw = tb[2] - tb[0]
        draw.text(((W - tw) / 2, y), line, font=font_tagline, fill=TEXT_SUB)
        y += 48

    # 하단 핸들 (최소 표기, 레터박스 바 바로 위)
    if instagram_handle:
        handle_text = f"@{instagram_handle}"
        hb = draw.textbbox((0, 0), handle_text, font=font_handle)
        hw = hb[2] - hb[0]
        draw.text(((W - hw) / 2, H - bar_h - 44), handle_text, font=font_handle, fill=TEXT_MUTED)

    img.save(output_path, format="JPEG", quality=100, subsampling=0, optimize=True)
    return output_path


def generate_detail_card(
    detail_title: str,
    detail_points: list[str],
    output_path: str,
    tag_text: str = "자세히 보기",
) -> str:
    """2번 슬라이드: 소제목 + 번호 매긴 상세 설명 4개 (다크 배경, 사진 없음)."""
    W, H = CARD_SIZE
    img = _dark_gradient_bg()
    draw = ImageDraw.Draw(img)

    font_title = _font(FONT_BOLD, 50)
    font_body = _font(FONT_REGULAR, 32)
    font_num = _font(FONT_BOLD, 30)
    font_tag = _font(FONT_BOLD, 26)

    _outline_pill(draw, tag_text, (MARGIN, 90), font_tag)

    y = 190
    draw.text((MARGIN, y), detail_title, font=font_title, fill=TEXT_MAIN)
    y += 96

    for i, point in enumerate([p for p in detail_points if p], 1):
        circle_r = 19
        draw.ellipse([MARGIN, y, MARGIN + circle_r * 2, y + circle_r * 2], outline=ACCENT, width=3)
        num_bbox = draw.textbbox((0, 0), str(i), font=font_num)
        nw = num_bbox[2] - num_bbox[0]
        draw.text((MARGIN + circle_r - nw / 2, y + circle_r - 21), str(i), font=font_num, fill=ACCENT)

        wrapped = textwrap.wrap(point, width=17)
        ty = y - 2
        for line in wrapped:
            draw.text((MARGIN + 60, ty), line, font=font_body, fill=TEXT_SUB)
            ty += 44
        y = max(ty, y + circle_r * 2 + 10) + 28

    img.save(output_path, format="JPEG", quality=100, subsampling=0, optimize=True)
    return output_path

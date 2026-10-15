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
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CARD_SIZE = (1080, 1080)
# 팔레트: 아이보리 + 버건디 메인, 올리브는 포인트로 소량
IVORY = (245, 239, 226)
IVORY_CARD = (252, 248, 238)
BURGUNDY = (110, 27, 43)
BURGUNDY_DEEP = (62, 14, 26)
OLIVE = (107, 114, 60)
OLIVE_LIGHT = (160, 168, 105)
INK = (44, 26, 30)

BG_TOP = (92, 21, 38)          # 버건디 그라데이션 (사진 없는 커버/클로징)
BG_BOTTOM = (46, 9, 20)
ACCENT = BURGUNDY
TEXT_MAIN = IVORY
TEXT_SUB = (236, 226, 208)
TEXT_MUTED = (205, 190, 170)
TEXT_FAINT = (190, 172, 150)

MARGIN = 150  # 좌우 안전 여백 (인스타 그리드 크롭 대비, 전체 폭의 약 14%)

# 폰트 경로: fonts/ 폴더에 나눔고딕 계열을 넣어서 사용합니다.
FONT_BOLD = "fonts/NanumGothicExtraBold.ttf"   # 없으면 NanumGothicBold.ttf로 대체
FONT_REGULAR = "fonts/NanumGothic.ttf"
# 제목/숫자/브랜드용 명조(세리프) - 고급스러운 인상. 없으면 고딕 볼드로 자동 대체
FONT_SERIF = "fonts/NanumMyeongjoBold.ttf"
# 제목용 굵은 고딕. Pretendard ExtraBold 권장(없으면 Bold → 나눔고딕 ExtraBold 순으로 자동 대체)
FONT_KO_TITLE = "fonts/Pretendard-ExtraBold.otf"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        f = ImageFont.truetype(path, size)
        if "Variable" in path:
            try:
                f.set_variation_by_axes([700])
            except Exception:
                pass
        return f
    except OSError:
        if "Pretendard" in path:
            for alt in ("fonts/Pretendard-Bold.otf", "fonts/Pretendard-SemiBold.otf", "fonts/NanumGothicExtraBold.ttf", "fonts/NanumGothicBold.ttf"):
                try:
                    return ImageFont.truetype(alt, size)
                except OSError:
                    pass
        if "Myeongjo" in path:
            for alt in ("fonts/NanumMyeongjoExtraBold.ttf", "fonts/NanumMyeongjo.ttf"):
                try:
                    return ImageFont.truetype(alt, size)
                except OSError:
                    pass
        try:
            return ImageFont.truetype("fonts/NanumGothicBold.ttf", size)
        except OSError:
            return ImageFont.load_default()


class MixedFont:
    """한글은 모던 고딕, 영문/숫자/기호는 세리프로 그리는 혼합 폰트."""

    def __init__(self, ko, en, tracking=0):
        self.ko, self.en, self.tracking = ko, en, tracking  # tracking: 글자 간격(px, 음수=좁게)


def _is_ko(ch: str) -> bool:
    return "\uac00" <= ch <= "\ud7a3" or "\u3130" <= ch <= "\u318f"


def _runs(text):
    runs, cur, cur_ko = [], "", None
    for ch in text:
        ko = _is_ko(ch)
        if ch == " " and cur_ko is not None:
            ko = cur_ko
        if cur_ko is None or ko == cur_ko:
            cur += ch
        else:
            runs.append((cur, cur_ko))
            cur = ch
        cur_ko = ko
    if cur:
        runs.append((cur, cur_ko))
    return runs


def _tlen(draw, text, font):
    if not isinstance(font, MixedFont):
        return draw.textlength(text, font=font)
    return sum(draw.textlength(t, font=font.ko if ko else font.en) for t, ko in _runs(text)) + font.tracking * len(text)


def _text(draw, xy, text, font, fill):
    """xy는 한글 폰트 기준 좌상단. 혼합 폰트는 공통 베이스라인에 맞춰 그립니다."""
    if not isinstance(font, MixedFont):
        draw.text(xy, text, font=font, fill=fill)
        return
    x, y = xy
    base = y + font.ko.getmetrics()[0]
    for t, ko in _runs(text):
        f = font.ko if ko else font.en
        for ch in t:
            draw.text((x, base), ch, font=f, fill=fill, anchor="ls")
            x += draw.textlength(ch, font=f) + font.tracking


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
    local_image_path: "str | None" = None,
    headline_highlight: str = "",
) -> str:
    """
    1번 슬라이드: 사진(있으면 전체 배경) + 아웃라인 태그 + 헤드라인 + 서브바.
    하단 중앙엔 본인 인스타그램 핸들(@instagram_handle)을 표시하고,
    출처는 우측 하단에 아주 작은 글씨로 최소화해서 표기합니다.

    local_image_path가 주어지면 image_url 대신 그 로컬 파일을 사진으로 사용합니다
    (텔레그램으로 직접 받은 사진 등, 이미 다운로드된 파일을 쓸 때 사용).
    """
    W, H = CARD_SIZE
    if local_image_path:
        try:
            photo = Image.open(local_image_path).convert("RGB")
        except Exception as e:
            print(f"[경고] 로컬 사진 열기 실패, 사진 없이 진행합니다: {e}")
            photo = None
    else:
        photo = _download_image(image_url)

    if photo is not None:
        img = _center_crop_resize(photo, W, H)
        # 하단에만 부드러운 중립 다크 그라데이션 (사진 상단은 원색 그대로)
        g_top = H - 700
        g_h = H - g_top
        overlay = Image.new("L", (W, g_h), 0)
        odraw = ImageDraw.Draw(overlay)
        for y in range(g_h):
            t = y / g_h
            a = t * t * (3 - 2 * t)          # smoothstep
            odraw.line([(0, y), (W, y)], fill=int(238 * a))
        img.paste(Image.new("RGB", (W, g_h), (12, 9, 10)), (0, g_top), overlay)
    else:
        img = _dark_gradient_bg()

    draw = ImageDraw.Draw(img)

    font_tag = _font(FONT_BOLD, 27)
    font_sub = _font(FONT_REGULAR, 30)
    font_handle = _font(FONT_REGULAR, 22)
    font_source = _font(FONT_REGULAR, 18)

    # 헤드라인: 굵은 고딕, 크게. 3줄 이내로 들어오도록 크기 자동 조절
    text_w = W - MARGIN * 2
    norm = " ".join(headline.split())
    hsize = 104
    while True:
        font_headline = _font(FONT_KO_TITLE, hsize)
        lines = _wrap_px(draw, norm, font_headline, text_w)
        if len(lines) <= 3 and (len(lines) <= 2 or hsize <= 80) or hsize <= 64:
            break
        hsize -= 4
    lines = lines[:3]
    line_h = int(hsize * 1.22)

    bottom_y = H - 92                      # 핸들/출처 줄
    rule_y = bottom_y - 26                 # 얇은 구분선
    sub_y = rule_y - 70                    # 요약 한 줄
    y_head = sub_y - 40 - len(lines) * line_h
    y_tag = y_head - 84

    # 태그: 버건디 채움 pill (아이보리 글자)
    x_cursor = MARGIN
    for tag in (tags or ["오늘의 뉴스"]):
        tb = draw.textbbox((0, 0), tag, font=font_tag)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        draw.rounded_rectangle([x_cursor, y_tag, x_cursor + tw + 44, y_tag + th + 26], radius=30, fill=BURGUNDY)
        draw.text((x_cursor + 22, y_tag + 11 - tb[1]), tag, font=font_tag, fill=IVORY)
        x_cursor += tw + 44 + 12

    # 헤드라인 그림자(가독성) → 형광펜 하이라이트 → 글자
    h0 = norm.find(headline_highlight) if headline_highlight else -1
    h1 = h0 + len(headline_highlight) if h0 >= 0 else -1
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    y = y_head
    for line in lines:
        sd.text((MARGIN + 2, y + 5), line, font=font_headline, fill=(0, 0, 0, 170))
        y += line_h
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(img)

    y = y_head
    offset = 0
    for line in lines:
        l0, l1 = offset, offset + len(line)
        seg0, seg1 = max(l0, h0), min(l1, h1)
        hi = h0 >= 0 and seg0 < seg1
        if hi:
            x0 = MARGIN + draw.textlength(line[: seg0 - l0], font=font_headline)
            x1 = MARGIN + draw.textlength(line[: seg1 - l0], font=font_headline)
            pad = int(hsize * 0.10)
            draw.rounded_rectangle(
                [x0 - pad, y + int(hsize * 0.10), x1 + pad, y + int(hsize * 1.12)],
                radius=int(hsize * 0.12), fill=IVORY,
            )
        if hi:
            pre, mid, post = line[: seg0 - l0], line[seg0 - l0: seg1 - l0], line[seg1 - l0:]
            x = MARGIN
            draw.text((x, y), pre, font=font_headline, fill=TEXT_MAIN)
            x += draw.textlength(pre, font=font_headline)
            draw.text((x, y), mid, font=font_headline, fill=BURGUNDY)
            x += draw.textlength(mid, font=font_headline)
            draw.text((x, y), post, font=font_headline, fill=TEXT_MAIN)
        else:
            draw.text((MARGIN, y), line, font=font_headline, fill=TEXT_MAIN)
        y += line_h
        offset = l1 + 1  # 줄바꿈으로 사라진 공백 1칸

    # 요약 한 줄 + 올리브 세로선
    draw.rectangle([MARGIN, sub_y + 3, MARGIN + 5, sub_y + 38], fill=OLIVE_LIGHT)
    draw.text((MARGIN + 22, sub_y), bullets[0] if bullets else "", font=font_sub, fill=(232, 224, 208))

    # 얇은 구분선 + 핸들 / 출처 (최소 표기)
    draw.line([(MARGIN, rule_y), (W - MARGIN, rule_y)], fill=(120, 108, 100), width=1)
    if instagram_handle:
        draw.text((MARGIN, bottom_y), f"@{instagram_handle}", font=font_handle, fill=(205, 195, 175))
    source_text = f"ⓒ{source_name}"
    sw = draw.textlength(source_text, font=font_source)
    draw.text((W - MARGIN - sw, bottom_y + 4), source_text, font=font_source, fill=(150, 140, 128))

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
    draw.rectangle([0, 0, W, bar_h], fill=OLIVE)
    draw.rectangle([0, H - bar_h, W, H], fill=OLIVE)

    font_logo = MixedFont(_font(FONT_KO_TITLE, 92), _font(FONT_SERIF, 100), tracking=-1)
    font_btn = _font(FONT_BOLD, 32)
    font_tagline = _font(FONT_REGULAR, 34)
    font_handle = _font(FONT_REGULAR, 22)

    # 중앙 브랜드 워드마크
    lw, lh = _tlen(draw, brand_name, font_logo), 100
    logo_y = H * 0.42
    _text(draw, ((W - lw) / 2, logo_y), brand_name, font_logo, TEXT_MAIN)

    # 팔로우 버튼 (아웃라인 pill)
    bb = draw.textbbox((0, 0), button_text, font=font_btn)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    pad_x, pad_y = 56, 20
    btn_w, btn_h = bw + pad_x * 2, bh + pad_y * 2
    btn_x = (W - btn_w) / 2
    btn_y = logo_y + lh + 64
    draw.rounded_rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h], radius=btn_h // 2, fill=IVORY)
    draw.text((btn_x + pad_x, btn_y + pad_y - 3), button_text, font=font_btn, fill=BURGUNDY)

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


HIGHLIGHT = (150, 28, 52)     # 숫자/핵심 수치 강조색 (진한 버건디)
CARD_BG = IVORY_CARD


def _wrap_px(draw, text, font, max_w):
    """픽셀 폭 기준 줄바꿈 (공백 단위, 너무 긴 단어는 글자 단위)."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if _tlen(draw, trial, font) <= max_w:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        cur = ""
        for ch in word:
            if _tlen(draw, cur + ch, font) > max_w:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
    if cur:
        lines.append(cur)
    return lines


def _draw_highlighted(draw, xy, line, font, base_fill):
    """숫자가 들어간 단어는 강조색으로 그립니다."""
    x, y = xy
    words = line.split(" ")
    for idx, w in enumerate(words):
        token = w + (" " if idx < len(words) - 1 else "")
        fill = HIGHLIGHT if any(c.isdigit() for c in w) else base_fill
        draw.text((x, y), token, font=font, fill=fill)
        x += draw.textlength(token, font=font)


def generate_detail_card(
    detail_title: str,
    detail_points: list[str],
    output_path: str,
    tag_text: str = "자세히 보기",
) -> str:
    """2번 슬라이드: 큰 후킹 제목 + 번호 카드 4개를 카드 전체 높이에 균등 배치."""
    W, H = CARD_SIZE
    img = Image.new("RGB", CARD_SIZE, IVORY)
    draw = ImageDraw.Draw(img)
    points = [p for p in detail_points if p][:4] or [""]
    n = len(points)

    # 상단 버건디 블록 + 올리브 포인트
    draw.rectangle([0, 0, W, 78], fill=BURGUNDY)
    draw.rectangle([0, 78, W, 84], fill=OLIVE)

    # 태그: 채워진 보라 pill
    font_tag = _font(FONT_BOLD, 26)
    tb = draw.textbbox((0, 0), tag_text, font=font_tag)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    draw.rounded_rectangle([MARGIN, 132, MARGIN + tw + 44, 132 + th + 26], radius=30, fill=BURGUNDY)
    draw.text((MARGIN + 22, 132 + 11 - tb[1]), tag_text, font=font_tag, fill=IVORY)

    # 제목 (크게, 최대 2줄, 마지막 줄 강조색)
    inner_w = W - MARGIN * 2
    tsize = 76
    while True:
        font_title = _font(FONT_KO_TITLE, tsize)
        tlines = _wrap_px(draw, detail_title, font_title, inner_w)
        if len(tlines) <= 2 or tsize <= 48:
            break
        tsize -= 4
    tlines = tlines[:2]
    ty = 210
    for li, line in enumerate(tlines):
        fill = BURGUNDY if (li == len(tlines) - 1 and len(tlines) > 1) else INK
        _text(draw, (MARGIN, ty), line, font_title, fill)
        ty += int(tsize * 1.28)
    # 제목 아래 포인트 바
    draw.rounded_rectangle([MARGIN, ty + 26, MARGIN + 90, ty + 34], radius=4, fill=OLIVE)

    # 번호 카드들: 남은 높이 전체를 균등 분배
    top = ty + 66
    bottom = H - 120
    gap = 16
    row_h = (bottom - top - gap * (n - 1)) // n
    row_h = min(row_h, 170)
    # 남는 공간이 있으면 위쪽 여백으로 분배해 세로 중앙감 확보
    used = row_h * n + gap * (n - 1)
    top += max(0, (bottom - top - used) // 2)

    num_w = 100
    for i, point in enumerate(points):
        y0 = top + i * (row_h + gap)
        draw.rounded_rectangle([MARGIN, y0, W - MARGIN, y0 + row_h], radius=24, fill=CARD_BG, outline=(224, 214, 192), width=2)
        draw.rounded_rectangle([MARGIN, y0 + 22, MARGIN + 7, y0 + row_h - 22], radius=3, fill=OLIVE)

        font_num = _font(FONT_KO_TITLE, 54)
        label = f"{i + 1:02d}"
        nb = draw.textbbox((0, 0), label, font=font_num)
        draw.text((MARGIN + 34, y0 + (row_h - (nb[3] - nb[1])) / 2 - nb[1]), label, font=font_num, fill=BURGUNDY)

        text_x = MARGIN + 34 + num_w + 10
        text_w = W - MARGIN - 28 - text_x
        bsize = 34
        while True:
            font_body = _font(FONT_REGULAR, bsize)
            blines = _wrap_px(draw, point, font_body, text_w)
            lh = int(bsize * 1.4)
            if len(blines) * lh <= row_h - 28 or bsize <= 24:
                break
            bsize -= 2
        block_h = len(blines) * lh
        by = y0 + (row_h - block_h) / 2 - (lh - bsize) / 2 + 2
        for line in blines:
            _draw_highlighted(draw, (text_x, by), line, font_body, INK)
            by += lh

    # 페이지 점 (2/3)
    cx, cy = W // 2, H - 70
    for k in range(4):
        on = k == 1
        r = 7
        x = cx + (k - 1.5) * 26
        draw.ellipse([x - r, cy - r, x + r, cy + r], fill=OLIVE if on else (205, 195, 172))

    img.save(output_path, format="JPEG", quality=100, subsampling=0, optimize=True)
    return output_path


def generate_direction_card(
    direction_title: str,
    direction_points: list[str],
    output_path: str,
    tag_text: str = "앞으로의 방향",
) -> str:
    """3번 슬라이드: 앞으로 취해야 할 방향성/지켜볼 포인트 (버건디 배경 + 아이보리 글자)."""
    W, H = CARD_SIZE
    img = _dark_gradient_bg()
    draw = ImageDraw.Draw(img)
    points = [p for p in direction_points if p][:3] or [""]
    n = len(points)
    inner_w = W - MARGIN * 2

    # 태그: 아이보리 pill
    font_tag = _font(FONT_BOLD, 26)
    tb = draw.textbbox((0, 0), tag_text, font=font_tag)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    draw.rounded_rectangle([MARGIN, 120, MARGIN + tw + 44, 120 + th + 26], radius=30, fill=IVORY)
    draw.text((MARGIN + 22, 120 + 11 - tb[1]), tag_text, font=font_tag, fill=BURGUNDY)

    # 제목 (최대 2줄)
    tsize = 76
    while True:
        font_title = _font(FONT_KO_TITLE, tsize)
        tlines = _wrap_px(draw, direction_title, font_title, inner_w)
        if len(tlines) <= 2 or tsize <= 48:
            break
        tsize -= 4
    ty = 200
    for line in tlines[:2]:
        _text(draw, (MARGIN, ty), line, font_title, TEXT_MAIN)
        ty += int(tsize * 1.28)
    draw.rounded_rectangle([MARGIN, ty + 26, MARGIN + 90, ty + 34], radius=4, fill=OLIVE_LIGHT)

    # 포인트: 카드 없이 큰 번호 + 본문 + 얇은 구분선, 남은 높이에 균등 분배
    top = ty + 80
    bottom = H - 130
    row_h = min((bottom - top) // n, 220)
    top += max(0, ((bottom - top) - row_h * n) // 2)
    font_num = _font(FONT_KO_TITLE, 62)
    for i, point in enumerate(points):
        y0 = top + i * row_h
        if i > 0:
            draw.line([(MARGIN, y0), (W - MARGIN, y0)], fill=(130, 70, 82), width=1)
        label = f"{i + 1:02d}"
        nb = draw.textbbox((0, 0), label, font=font_num)
        draw.text((MARGIN, y0 + (row_h - (nb[3] - nb[1])) / 2 - nb[1]), label, font=font_num, fill=OLIVE_LIGHT)
        text_x = MARGIN + 120
        text_w = W - MARGIN - text_x
        bsize = 36
        while True:
            font_body = _font(FONT_REGULAR, bsize)
            blines = _wrap_px(draw, point, font_body, text_w)
            lh = int(bsize * 1.42)
            if len(blines) * lh <= row_h - 36 or bsize <= 26:
                break
            bsize -= 2
        by = y0 + (row_h - len(blines) * lh) / 2 - (lh - bsize) / 2 + 2
        for line in blines:
            words = line.split(" ")
            x = text_x
            for idx, w in enumerate(words):
                token = w + (" " if idx < len(words) - 1 else "")
                fill = OLIVE_LIGHT if any(c.isdigit() for c in w) else TEXT_MAIN
                draw.text((x, by), token, font=font_body, fill=fill)
                x += draw.textlength(token, font=font_body)
            by += lh

    # 페이지 점 (3/4)
    cx, cy = W // 2, H - 70
    for k in range(4):
        x = cx + (k - 1.5) * 26
        draw.ellipse([x - 7, cy - 7, x + 7, cy + 7], fill=IVORY if k == 2 else (140, 80, 92))

    img.save(output_path, format="JPEG", quality=100, subsampling=0, optimize=True)
    return output_path


def generate_story_card(
    cover_path: str,
    output_path: str,
    instagram_handle: str = "",
    label: str = "NEW POST",
) -> str:
    """스토리용 9:16(1080x1920) 이미지: 커버 카드를 가운데 놓고 위아래를 브랜드 배경으로 채웁니다.
    스토리 UI가 가리는 상단/하단 약 250px 안쪽은 비워 둡니다."""
    SW, SH = 1080, 1920
    img = Image.new("RGB", (SW, SH), BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(SH):
        t = y / SH
        d.line([(0, y), (SW, y)], fill=tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)))

    cover = Image.open(cover_path).convert("RGB")
    cw = SW
    ch = int(cover.height * cw / cover.width)
    cover = cover.resize((cw, ch), Image.LANCZOS)
    cy = (SH - ch) // 2
    img.paste(cover, (0, cy))
    d.rectangle([0, cy - 5, SW, cy - 1], fill=OLIVE)
    d.rectangle([0, cy + ch, SW, cy + ch + 4], fill=OLIVE)

    # 상단 라벨 (안전영역 안쪽)
    font_label = _font(FONT_SERIF, 54)
    lw = d.textlength(label, font=font_label)
    d.text(((SW - lw) / 2, 270), label, font=font_label, fill=IVORY)
    d.rounded_rectangle([SW / 2 - 45, 352, SW / 2 + 45, 360], radius=4, fill=OLIVE_LIGHT)

    # 하단 안내 + 핸들
    font_cta = _font(FONT_BOLD, 38)
    cta = "피드에서 전체 카드 보기"
    cw2 = d.textlength(cta, font=font_cta)
    d.text(((SW - cw2) / 2, 1565), cta, font=font_cta, fill=IVORY)
    if instagram_handle:
        font_h = _font(FONT_REGULAR, 30)
        ht = f"@{instagram_handle}"
        hw = d.textlength(ht, font=font_h)
        d.text(((SW - hw) / 2, 1630), ht, font=font_h, fill=(205, 190, 170))

    img.save(output_path, format="JPEG", quality=100, subsampling=0, optimize=True)
    return output_path

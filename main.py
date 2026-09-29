"""
전체 파이프라인 실행 스크립트.

흐름:
1. 대기 중인 "인물 기사"가 있으면 → 텔레그램에 사진 답장이 왔는지 확인
   - 왔으면: 그 사진으로 카드뉴스 완성 → 게시 → 대기 해제
   - 안 왔으면: 이번 실행은 여기서 종료 (새 기사 안 가져옴)
2. 대기 중인 게 없으면 → RSS에서 최신 기사 수집 → 화제성 있는 기사 선택
3. Claude로 카드뉴스 콘텐츠 생성 (인물 중심 기사인지도 함께 판단)
4. 인물 중심 기사면 → 텔레그램으로 알림 보내고 대기 상태로 저장 후 종료
   (자동으로 아무 사진이나 붙이지 않고, 반드시 사람이 확인한 사진만 사용)
5. 인물 중심이 아니면 → Pexels에서 관련 무료 이미지 검색해서 완전 자동 진행

실행: python3 main.py
스케줄링:
- 메인 스케줄(하루 몇 번): 새 기사 확인 + 인물기사면 알림
- 별도의 잦은 스케줄(예: 10분마다): 사진 답장이 왔는지 확인하는 용도로도 이 스크립트를 그대로 실행
"""

import os
import sys

from config import (
    RSS_FEED_URL,
    SOURCE_NAME,
    IG_USER_ID,
    IG_ACCESS_TOKEN,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_UPLOAD_PRESET,
    PEXELS_API_KEY,
    UNSPLASH_ACCESS_KEY,
    INSTAGRAM_HANDLE,
    BRAND_NAME,
    CTA_TAGLINE,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from fetch_news import fetch_latest_articles
from summarize import summarize_for_card, build_caption, pick_hottest_article
from generate_card import generate_cover_card, generate_detail_card, generate_closing_card
from post_instagram import upload_image, post_carousel
from history import load_history, save_to_history
from stock_image import search_related_photo
from telegram_notify import send_message, check_for_photo_reply
from pending import save_pending, load_pending, clear_pending


def _build_and_post(title, link, content, image_url=None, local_image_path=None, photo_attribution=None):
    """카드 3장 생성 → 업로드 → 캐러셀 게시까지 공통 처리."""
    os.makedirs("output", exist_ok=True)
    slug = abs(hash(link))

    print("[카드 생성] 커버 카드(사진+헤드라인) 생성 중...")
    cover_path = f"output/cover_{slug}.jpg"
    generate_cover_card(
        headline=content["headline"],
        bullets=content["bullets"],
        source_name=SOURCE_NAME,
        image_url=image_url,
        local_image_path=local_image_path,
        output_path=cover_path,
        instagram_handle=INSTAGRAM_HANDLE,
        tags=[content.get("tag", "주목")],
    )

    print("[카드 생성] 상세 카드(설명) 생성 중...")
    detail_path = f"output/detail_{slug}.jpg"
    generate_detail_card(
        detail_title=content.get("detail_title", "자세히 보기"),
        detail_points=content.get("detail_points", []),
        output_path=detail_path,
    )

    print("[카드 생성] 클로징 카드(CTA) 생성 중...")
    closing_path = f"output/closing_{slug}.jpg"
    generate_closing_card(
        brand_name=BRAND_NAME,
        tagline=CTA_TAGLINE,
        output_path=closing_path,
        instagram_handle=INSTAGRAM_HANDLE,
    )

    print("[업로드] 이미지 3장 업로드 중...")
    cover_url = upload_image(cover_path, CLOUDINARY_CLOUD_NAME, CLOUDINARY_UPLOAD_PRESET)
    detail_url = upload_image(detail_path, CLOUDINARY_CLOUD_NAME, CLOUDINARY_UPLOAD_PRESET)
    closing_url = upload_image(closing_path, CLOUDINARY_CLOUD_NAME, CLOUDINARY_UPLOAD_PRESET)

    print("[게시] Instagram에 캐러셀 게시 중...")
    caption = build_caption(
        title, link, SOURCE_NAME,
        bullets=content.get("bullets"),
        detail_points=content.get("detail_points"),
        outlook=content.get("outlook", ""),
    )
    if photo_attribution:
        caption += f"\n{photo_attribution}"
    media_id = post_carousel(
        image_urls=[cover_url, detail_url, closing_url],
        caption=caption,
        ig_user_id=IG_USER_ID,
        access_token=IG_ACCESS_TOKEN,
    )
    print(f"  → 게시 완료! media_id: {media_id}")
    save_to_history(link)


def run():
    # ── 1) 대기 중인 인물 기사가 있는지 먼저 확인 ──────────────────
    pending = load_pending()
    if pending:
        print("[대기 확인] 인물 기사가 사진 답장을 기다리고 있습니다. 텔레그램 확인 중...")
        photo_path = check_for_photo_reply(
            TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, save_path="output/telegram_photo.jpg"
        )
        if not photo_path:
            print("아직 사진 답장이 없습니다. 다음 실행 때 다시 확인합니다.")
            return

        print("사진 도착! 이 사진으로 카드뉴스를 완성해 게시합니다.")
        _build_and_post(
            title=pending["title"],
            link=pending["link"],
            content=pending["content"],
            local_image_path=photo_path,
        )
        clear_pending()
        print("완료.")
        return

    # ── 2) 대기 중인 게 없으면 평소처럼 새 기사 수집 ──────────────
    print("[1/4] 최신 기사 수집 중...")
    articles = fetch_latest_articles(RSS_FEED_URL, limit=10)
    if not articles:
        print("가져올 기사가 없습니다. RSS URL을 확인하세요.")
        return

    posted = load_history()
    candidates = [a for a in articles if a.link not in posted]
    if not candidates:
        print("게시할 새 기사가 없습니다 (모두 이미 게시됨).")
        return

    if len(candidates) == 1:
        target = candidates[0]
    else:
        print(f"  → 후보 {len(candidates)}개 중 화제성 있는 기사를 Claude가 고릅니다...")
        target = candidates[pick_hottest_article(candidates)]

    print(f"[2/4] 선택된 기사: {target.title}")

    print("[3/4] Claude로 카드뉴스 콘텐츠 생성 중...")
    content = summarize_for_card(target.title, target.summary)

    # ── 3) 특정 인물 중심 기사면 자동 게시 대신 텔레그램으로 확인 요청 ──
    if content.get("is_person_focused"):
        print("  → 특정 인물이 중심인 기사입니다. 자동으로 사진을 붙이지 않고 확인을 요청합니다.")
        save_pending(target.link, target.title, target.summary, content)
        send_message(
            TELEGRAM_BOT_TOKEN,
            TELEGRAM_CHAT_ID,
            (
                "📸 인물 관련 기사를 발견했어요, 사진이 필요해요!\n\n"
                f"제목: {target.title}\n"
                f"헤드라인: {content['headline']}\n"
                f"원문: {target.link}\n\n"
                "이 채팅에 어울리는 사진을 답장으로 보내주시면, "
                "다음 확인 때 자동으로 카드뉴스를 만들어 게시할게요."
            ),
        )
        print("텔레그램으로 알림을 보냈습니다. 사진 답장을 기다립니다.")
        return

    # ── 4) 인물 중심이 아니면 기존처럼 완전 자동 진행 ────────────
    print("[4/4] Pexels/Unsplash에서 관련 이미지를 검색합니다...")
    photo_result = search_related_photo(content.get("image_query", ""), PEXELS_API_KEY, UNSPLASH_ACCESS_KEY)
    image_url = photo_result["url"] if photo_result else None
    photo_attribution = photo_result["attribution"] if photo_result else None
    if not image_url:
        print("  → 관련 이미지를 못 찾아 텍스트만으로 진행합니다.")

    _build_and_post(target.title, target.link, content, image_url=image_url, photo_attribution=photo_attribution)
    print("완료.")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"[에러] 파이프라인 실행 중 문제 발생: {e}", file=sys.stderr)
        sys.exit(1)

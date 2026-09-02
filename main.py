"""
전체 파이프라인 실행 스크립트 (캐러셀 2장 버전).

흐름:
1. RSS에서 최신 기사 목록 수집
2. 아직 게시하지 않은 기사 중 첫 번째 선택
3. Claude API로 커버용 헤드라인/불릿 + 상세용 포인트 생성
4. Pillow로 커버 카드(사진+헤드라인) + 상세 카드(설명) 2장 생성
5. 두 이미지를 호스팅에 업로드해 공개 URL 확보
6. Instagram Graph API로 캐러셀(2장) 게시
7. 게시 이력 저장 (중복 방지)

실행: python3 main.py
스케줄링: cron 또는 GitHub Actions로 이 스크립트를 정해진 시간마다 실행
"""

import os
import sys

from config import (
    RSS_FEED_URL,
    SOURCE_NAME,
    IG_USER_ID,
    IG_ACCESS_TOKEN,
    IMGBB_API_KEY,
    PEXELS_API_KEY,
)
from fetch_news import fetch_latest_articles
from summarize import summarize_for_card, build_caption
from generate_card import generate_cover_card, generate_detail_card
from post_instagram import upload_image, post_carousel
from history import load_history, save_to_history
from stock_image import search_related_photo


def run():
    print("[1/7] 최신 기사 수집 중...")
    articles = fetch_latest_articles(RSS_FEED_URL, limit=10)
    if not articles:
        print("가져올 기사가 없습니다. RSS URL을 확인하세요.")
        return

    posted = load_history()
    target = next((a for a in articles if a.link not in posted), None)
    if target is None:
        print("게시할 새 기사가 없습니다 (모두 이미 게시됨).")
        return

    print(f"[2/7] 선택된 기사: {target.title}")

    print("[3/7] Claude로 카드뉴스 콘텐츠 생성 중...")
    content = summarize_for_card(target.title, target.summary)

    # 기사에 사진이 없으면 헤드라인 키워드로 관련 무료 스톡 이미지를 검색
    image_url = target.image_url
    if not image_url:
        print("  → 기사에 사진이 없어 관련 이미지를 검색합니다...")
        image_url = search_related_photo(content["headline"], target.title, PEXELS_API_KEY)
        if image_url:
            print(f"  → 관련 이미지 찾음: {image_url}")
        else:
            print("  → 관련 이미지를 못 찾아 텍스트만으로 진행합니다.")

    os.makedirs("output", exist_ok=True)
    slug = abs(hash(target.link))

    print("[4/7] 커버 카드(사진+헤드라인) 생성 중...")
    cover_path = f"output/cover_{slug}.jpg"
    generate_cover_card(
        headline=content["headline"],
        bullets=content["bullets"],
        source_name=SOURCE_NAME,
        image_url=image_url,
        output_path=cover_path,
    )

    print("[5/7] 상세 카드(설명) 생성 중...")
    detail_path = f"output/detail_{slug}.jpg"
    generate_detail_card(
        detail_title=content.get("detail_title", "자세히 보기"),
        detail_points=content.get("detail_points", []),
        output_path=detail_path,
    )

    print("[6/7] 이미지 2장 업로드 중...")
    cover_url = upload_image(cover_path, IMGBB_API_KEY)
    detail_url = upload_image(detail_path, IMGBB_API_KEY)
    print(f"  → 커버: {cover_url}")
    print(f"  → 상세: {detail_url}")

    print("[7/7] Instagram에 캐러셀 게시 중...")
    caption = build_caption(target.title, target.link, SOURCE_NAME)
    media_id = post_carousel(
        image_urls=[cover_url, detail_url],
        caption=caption,
        ig_user_id=IG_USER_ID,
        access_token=IG_ACCESS_TOKEN,
    )
    print(f"  → 게시 완료! media_id: {media_id}")

    save_to_history(target.link)
    print("완료.")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"[에러] 파이프라인 실행 중 문제 발생: {e}", file=sys.stderr)
        sys.exit(1)

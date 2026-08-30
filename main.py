"""
전체 파이프라인 실행 스크립트.

흐름:
1. RSS에서 최신 기사 목록 수집
2. 아직 게시하지 않은 기사 중 첫 번째 선택
3. Claude API로 카드뉴스용 요약 생성
4. Pillow로 카드뉴스 이미지 생성
5. 이미지를 호스팅에 업로드해 공개 URL 확보
6. Instagram Graph API로 게시
7. 게시 이력 저장 (중복 방지)

실행: python main.py
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
)
from fetch_news import fetch_latest_articles
from summarize import summarize_for_card, build_caption
from generate_card import generate_card
from post_instagram import upload_image, post_to_instagram
from history import load_history, save_to_history


def run():
    print("[1/6] 최신 기사 수집 중...")
    articles = fetch_latest_articles(RSS_FEED_URL, limit=10)
    if not articles:
        print("가져올 기사가 없습니다. RSS URL을 확인하세요.")
        return

    posted = load_history()
    target = next((a for a in articles if a.link not in posted), None)
    if target is None:
        print("게시할 새 기사가 없습니다 (모두 이미 게시됨).")
        return

    print(f"[2/6] 선택된 기사: {target.title}")

    print("[3/6] Claude로 카드뉴스 요약 생성 중...")
    summary = summarize_for_card(target.title, target.summary)

    print("[4/6] 카드뉴스 이미지 생성 중...")
    os.makedirs("output", exist_ok=True)
    image_path = f"output/card_{abs(hash(target.link))}.jpg"
    generate_card(
        headline=summary["headline"],
        bullets=summary["bullets"],
        source_name=SOURCE_NAME,
        output_path=image_path,
    )

    print("[5/6] 이미지 업로드 중...")
    image_url = upload_image(image_path, IMGBB_API_KEY)
    print(f"  → 업로드 완료: {image_url}")

    print("[6/6] Instagram에 게시 중...")
    caption = build_caption(target.title, target.link, SOURCE_NAME)
    media_id = post_to_instagram(
        image_url=image_url,
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

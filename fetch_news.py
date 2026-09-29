"""
RSS 피드에서 최신 뉴스 기사를 가져오는 모듈.

기본값은 연합뉴스 전체 뉴스 RSS입니다.
다른 언론사로 바꾸려면 config.py의 RSS_FEED_URL만 수정하면 됩니다.

주요 언론사 RSS 예시 (반드시 각 언론사의 이용약관/robots.txt를 확인하세요):
- 연합뉴스 전체    : https://www.yna.co.kr/rss/news.xml
- 연합뉴스 IT/과학  : https://www.yna.co.kr/rss/it.xml
- 한겨레 전체      : https://www.hani.co.kr/rss/
- KBS 전체        : http://world.kbs.co.kr/rss/rss_news.htm?lang=k
"""

import re
import feedparser
import requests
from dataclasses import dataclass
from typing import Optional

# XML 1.0 규격상 허용되지 않는 제어문자 (언론사 서버가 가끔 이런 문자를 이스케이프 없이
# 그대로 흘려보내서 "not well-formed (invalid token)" 에러가 나는 경우가 있음)
_INVALID_XML_CHARS = re.compile(
    "[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)


@dataclass
class Article:
    title: str
    link: str
    summary: str
    published: str
    image_url: Optional[str] = None


def fetch_latest_articles(feed_url: str, limit: int = 10) -> list[Article]:
    """RSS 피드를 파싱해서 최신 기사 목록을 반환합니다."""
    feed = None

    # 1차: feedparser로 바로 파싱 시도 (대부분의 경우 이걸로 충분)
    feed = feedparser.parse(feed_url)

    # 2차: 파싱에 문제가 있었거나 기사를 하나도 못 가져왔으면,
    # 직접 다운로드해서 깨진 제어문자를 제거한 뒤 재시도
    if feed.bozo or not feed.entries:
        print(f"[경고] RSS 1차 파싱 실패 또는 결과 없음, 정제 후 재시도합니다: {feed.bozo_exception if feed.bozo else '기사 0개'}")
        try:
            resp = requests.get(feed_url, timeout=15)
            resp.raise_for_status()
            cleaned = _INVALID_XML_CHARS.sub("", resp.text)
            retried = feedparser.parse(cleaned)
            if retried.entries:
                feed = retried
                print(f"  → 정제 후 재파싱 성공, 기사 {len(feed.entries)}개 확보")
            else:
                print("  → 정제 후에도 기사를 못 가져왔습니다. RSS URL을 확인해주세요.")
        except Exception as e:
            print(f"  → 재시도 중 오류: {e}")

    articles = []
    for entry in feed.entries[:limit]:
        image_url = None
        # RSS 표준에 따라 이미지 위치가 다를 수 있어 여러 케이스를 확인
        if "media_content" in entry and entry.media_content:
            image_url = entry.media_content[0].get("url")
        elif "media_thumbnail" in entry and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get("url")
        elif "enclosures" in entry and entry.enclosures:
            image_url = entry.enclosures[0].get("href")

        articles.append(
            Article(
                title=entry.get("title", "").strip(),
                link=entry.get("link", "").strip(),
                summary=entry.get("summary", "").strip(),
                published=entry.get("published", ""),
                image_url=image_url,
            )
        )
    return articles


if __name__ == "__main__":
    # 단독 실행 시 테스트용 출력
    from config import RSS_FEED_URL

    for a in fetch_latest_articles(RSS_FEED_URL, limit=5):
        print(f"- {a.title} ({a.link})")

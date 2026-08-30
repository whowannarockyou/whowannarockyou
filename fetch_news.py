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

import feedparser
from dataclasses import dataclass
from typing import Optional


@dataclass
class Article:
    title: str
    link: str
    summary: str
    published: str
    image_url: Optional[str] = None


def fetch_latest_articles(feed_url: str, limit: int = 10) -> list[Article]:
    """RSS 피드를 파싱해서 최신 기사 목록을 반환합니다."""
    feed = feedparser.parse(feed_url)

    if feed.bozo:
        print(f"[경고] RSS 파싱 중 문제가 발생했을 수 있습니다: {feed.bozo_exception}")

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

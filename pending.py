"""
인물 관련 기사를 발견했을 때, 사진 답장이 올 때까지 "대기 상태"로 저장해둡니다.
한 번에 하나의 기사만 대기시킵니다 (여러 개 동시 대기는 복잡도만 올라가므로 단순하게 유지).
"""

import json
import os

PENDING_FILE = "pending_photo.json"


def save_pending(article_link: str, article_title: str, article_summary: str, content: dict) -> None:
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "link": article_link,
                "title": article_title,
                "summary": article_summary,
                "content": content,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def load_pending() -> "dict | None":
    if not os.path.exists(PENDING_FILE):
        return None
    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def clear_pending() -> None:
    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)

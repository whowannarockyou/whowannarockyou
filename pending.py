"""
인물 관련 기사를 발견했을 때, 사진 답장이 올 때까지 "대기 상태"로 저장해둡니다.
한 번에 하나의 기사만 대기시킵니다 (여러 개 동시 대기는 복잡도만 올라가므로 단순하게 유지).

너무 오래 답장이 없으면(타임아웃) 그 기사는 포기하고 다른 새 기사 처리를 재개할 수 있도록
요청 시각(requested_at)을 함께 기록합니다.
"""

import json
import os
import time

PENDING_FILE = "pending_photo.json"


def save_pending(article_link: str, article_title: str, article_summary: str, content: dict) -> None:
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "link": article_link,
                "title": article_title,
                "summary": article_summary,
                "content": content,
                "requested_at": time.time(),  # 유닉스 타임스탬프(초)
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


def is_expired(pending: dict, timeout_minutes: float) -> bool:
    """
    대기 시작 후 timeout_minutes(분)가 지났으면 True.
    requested_at이 없는 예전 형식의 대기 파일은 안전하게 '만료 안 됨'으로 처리합니다.
    """
    requested_at = pending.get("requested_at")
    if requested_at is None:
        return False
    elapsed_minutes = (time.time() - requested_at) / 60
    return elapsed_minutes >= timeout_minutes

"""이미 게시한 기사 링크를 기록해서 중복 게시를 방지합니다."""

import json
import os

HISTORY_FILE = "posted_history.json"


def load_history() -> set[str]:
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_to_history(link: str) -> None:
    history = load_history()
    history.add(link)
    # 이력이 너무 커지지 않도록 최근 500개만 유지
    trimmed = list(history)[-500:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)

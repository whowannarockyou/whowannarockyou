"""
텔레그램 봇 API로 알림을 보내고, 사용자가 보낸 사진 답장을 확인합니다.

봇 생성: 텔레그램에서 @BotFather 검색 → /newbot → 봇 이름 입력 → Bot Token 발급
chat_id 확인: 만든 봇에게 아무 메시지나 먼저 보낸 뒤,
  https://api.telegram.org/bot<TOKEN>/getUpdates 를 브라우저로 열면
  "chat":{"id": 숫자} 부분에서 확인 가능
"""

import os
import json
import requests

BASE_URL = "https://api.telegram.org/bot{token}"
STATE_FILE = "telegram_state.json"


def send_message(bot_token: str, chat_id: str, text: str) -> None:
    """텔레그램으로 알림 메시지를 보냅니다."""
    url = BASE_URL.format(token=bot_token) + "/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=15)


def _load_last_update_id() -> int:
    if not os.path.exists(STATE_FILE):
        return 0
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("last_update_id", 0)


def _save_last_update_id(update_id: int) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_update_id": update_id}, f)


def check_for_photo_reply(bot_token: str, chat_id: str, save_path: str) -> "str | None":
    """
    사용자가 보낸 새 사진 메시지가 있는지 확인합니다.
    있으면 save_path에 다운로드하고 그 경로를 반환, 없으면 None을 반환합니다.
    이미 처리한 메시지는 telegram_state.json에 기록해서 중복 처리하지 않습니다.
    """
    last_id = _load_last_update_id()
    url = BASE_URL.format(token=bot_token) + "/getUpdates"
    resp = requests.get(url, params={"offset": last_id + 1, "timeout": 0}, timeout=15)
    resp.raise_for_status()
    updates = resp.json().get("result", [])

    photo_file_id = None
    max_update_id = last_id

    for update in updates:
        max_update_id = max(max_update_id, update["update_id"])
        message = update.get("message", {})
        if str(message.get("chat", {}).get("id")) != str(chat_id):
            continue
        if "photo" in message:
            # photo는 여러 해상도로 오는데, 마지막이 가장 고화질
            photo_file_id = message["photo"][-1]["file_id"]

    _save_last_update_id(max_update_id)

    if not photo_file_id:
        return None

    # file_id로 실제 다운로드 경로 조회 후 다운로드
    file_info_url = BASE_URL.format(token=bot_token) + "/getFile"
    file_resp = requests.get(file_info_url, params={"file_id": photo_file_id}, timeout=15)
    file_resp.raise_for_status()
    file_path = file_resp.json()["result"]["file_path"]

    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    img_resp = requests.get(download_url, timeout=30)
    img_resp.raise_for_status()

    with open(save_path, "wb") as f:
        f.write(img_resp.content)

    return save_path

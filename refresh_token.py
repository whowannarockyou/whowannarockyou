"""
장기 액세스 토큰을 갱신합니다. Instagram 장기 토큰은 발급 후 24시간이 지나야,
그리고 만료 전이어야 갱신할 수 있습니다. 30~45일마다 실행하는 것을 권장합니다.
"""

import requests
from config import IG_ACCESS_TOKEN

resp = requests.get(
    "https://graph.instagram.com/refresh_access_token",
    params={
        "grant_type": "ig_refresh_token",
        "access_token": IG_ACCESS_TOKEN,
    },
)
resp.raise_for_status()
data = resp.json()

print("갱신 완료. config.py의 IG_ACCESS_TOKEN을 아래 값으로 교체하세요:")
print(f'IG_ACCESS_TOKEN = "{data["access_token"]}"')
print(f'(새 만료까지 {data["expires_in"]}초 남음 ≈ {data["expires_in"] // 86400}일)')

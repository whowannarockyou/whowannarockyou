"""
Instagram 비즈니스 로그인(Instagram API with Instagram Login)으로
Long-lived Access Token과 Instagram User ID를 발급받는 헬퍼 스크립트.

사용 순서:
1. Meta 앱 대시보드 > Instagram > API 설정에서 아래 값을 확인:
   - Instagram 앱 ID
   - Instagram 앱 시크릿
   - Business login settings > Redirect URI (redirect-page/index.html을 배포한 URL)
2. 이 스크립트를 실행하면 로그인 URL이 출력됩니다. 브라우저에 붙여넣고 로그인.
3. 로그인 완료 후 리디렉트된 페이지에서 'code' 값을 복사.
4. 이 스크립트에 code를 붙여넣으면 자동으로 토큰 교환 및 IG User ID 조회까지 진행됩니다.
"""

import requests

APP_ID = input("Instagram 앱 ID: ").strip()
APP_SECRET = input("Instagram 앱 시크릿: ").strip()
REDIRECT_URI = input("등록한 Redirect URI (예: https://yourname.github.io/insta-news-bot/): ").strip()

SCOPES = "instagram_business_basic,instagram_business_content_publish"

auth_url = (
    "https://www.instagram.com/oauth/authorize"
    f"?client_id={APP_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&response_type=code"
    f"&scope={SCOPES}"
)

print("\n1) 아래 URL을 브라우저에 열고 인스타그램 계정으로 로그인 후 권한을 승인하세요:\n")
print(auth_url)
print("\n2) 로그인 완료 후 리디렉트된 페이지에 표시되는 code 값을 아래에 붙여넣으세요.\n")

code = input("code: ").strip()

# 1단계: 인증 코드 -> 단기(1시간) 액세스 토큰
short_lived_resp = requests.post(
    "https://api.instagram.com/oauth/access_token",
    data={
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    },
)
short_lived_resp.raise_for_status()
short_data = short_lived_resp.json()
short_token = short_data["access_token"]
ig_user_id = short_data.get("user_id")
print(f"\n단기 토큰 발급 완료. Instagram User ID: {ig_user_id}")

# 2단계: 단기 토큰 -> 장기(60일) 액세스 토큰
long_lived_resp = requests.get(
    "https://graph.instagram.com/access_token",
    params={
        "grant_type": "ig_exchange_token",
        "client_secret": APP_SECRET,
        "access_token": short_token,
    },
)
long_lived_resp.raise_for_status()
long_data = long_lived_resp.json()
long_token = long_data["access_token"]

print("\n=== 발급 완료! config.py에 아래 값을 입력하세요 ===")
print(f"IG_USER_ID = \"{ig_user_id}\"")
print(f"IG_ACCESS_TOKEN = \"{long_token}\"")
print(f"\n(이 토큰은 60일 후 만료됩니다. 만료 전 refresh_token.py로 갱신하세요.)")

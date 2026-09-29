# 이 파일을 config.py로 복사한 뒤 실제 값을 채워넣으세요.
# config.py는 .gitignore에 반드시 포함시켜서 깃허브에 올라가지 않게 하세요.

# 1) 뉴스 소스
RSS_FEED_URL = "https://www.yna.co.kr/rss/news.xml"
SOURCE_NAME = "연합뉴스"

# 2) Instagram Graph API
IG_USER_ID = "28052535914410541"
IG_ACCESS_TOKEN = "IGAAVzhj61wWhBZAFk4Q2o4SkRvTmtXVndPckN5WlllZA05OZA1NXYkZAHeExGaDBYbzNZAbXNHQkJoUUhrNzFqd3BYOUxDMTVWc3gyRG5LTDRUeGVOSl91QWhqUUhkaV9TaDVLaU1oT2xFV3JJdVcxa192WDlB"

# 3) 이미지 호스팅 (Cloudinary 무료 티어)
# https://cloudinary.com 가입 → 대시보드에서 "Cloud name" 확인
# Settings(설정) → Upload → "Add upload preset" → Signing Mode를 반드시 "Unsigned"로 설정 → Save
CLOUDINARY_CLOUD_NAME = "x4wgndeb"
CLOUDINARY_UPLOAD_PRESET = "wanna rock"

# 4) 관련 이미지 검색 (Pexels 무료 API 키, https://www.pexels.com/api 에서 발급)
# 기사에 자체 사진이 없을 때, 헤드라인 키워드로 관련 무료 스톡 이미지를 찾는 데 사용됩니다.
PEXELS_API_KEY = "jD56ytdVrP3TqgP6xMV50JYrWZCfYsfxnWmNX8hM9RTYyLtr4wb4Z1F6"

# 4-1) 관련 이미지 검색 (Unsplash Access Key)
# https://unsplash.com/oauth/applications 접속 → 무료 가입 → "New Application" → Access Key 발급
# (API 이용약관상 사용 시 촬영자 크레딧 표기가 필수라 캡션에 자동으로 추가됩니다)
UNSPLASH_ACCESS_KEY = "LaNPqvW7T9CpTyGIiydj_kt8ux08QYAeEXdU9p0zWYI"

# 5) Claude API (요약용)
# 환경변수 ANTHROPIC_API_KEY 로 설정하는 것을 권장 (이 파일에 직접 쓰지 마세요)

# 6) 카드 하단에 표시할 본인 인스타그램 계정 (@ 제외하고 아이디만)
INSTAGRAM_HANDLE = "wannarockyou.mag"

# 7) 클로징 슬라이드(3번째 장)용 브랜드 워드마크 / CTA 문구
BRAND_NAME = "@wannarockyour.mag."
CTA_TAGLINE = "다음 소식이 궁금하다면?."

# 8) 텔레그램 봇 (인물 관련 기사 발견 시 사진 요청 알림용)
# @BotFather에게 /newbot 으로 봇 생성 → Bot Token 발급
# 만든 봇에게 메시지 하나 보낸 뒤 https://api.telegram.org/bot<TOKEN>/getUpdates 접속 → chat id 확인
TELEGRAM_BOT_TOKEN = "8626252144:AAEMTh6R2bGLknw2mWbY09aptpTDYitqEGQ"
TELEGRAM_CHAT_ID = "8466240463"

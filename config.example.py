# 이 파일을 config.py로 복사한 뒤 실제 값을 채워넣으세요.
# config.py는 .gitignore에 반드시 포함시켜서 깃허브에 올라가지 않게 하세요.

# 1) 뉴스 소스
RSS_FEED_URL = "https://www.yna.co.kr/rss/news.xml"
SOURCE_NAME = "연합뉴스"

# 1-1) (선택) 여러 피드를 합쳐서 후보로 쓰고 싶을 때. 이 값이 있으면 RSS_FEED_URL 대신 사용됩니다.
# 예: 종합 뉴스 + 연예 뉴스. 연예 피드 주소는 해당 언론사 RSS 안내 페이지에서 꼭 확인하세요.
# RSS_FEED_URLS = [
#     "https://www.yna.co.kr/rss/news.xml",
#     "https://www.yna.co.kr/rss/entertainment.xml",
# ]

# 2) Instagram Graph API
IG_USER_ID = "your_instagram_business_account_id"
IG_ACCESS_TOKEN = "your_long_lived_access_token"

# 3) 이미지 호스팅 (Cloudinary 무료 티어)
# https://cloudinary.com 가입 → 대시보드에서 "Cloud name" 확인
# Settings(설정) → Upload → "Add upload preset" → Signing Mode를 반드시 "Unsigned"로 설정 → Save
CLOUDINARY_CLOUD_NAME = "your_cloud_name"
CLOUDINARY_UPLOAD_PRESET = "your_unsigned_upload_preset_name"

# 4) 관련 이미지 검색 (Pexels 무료 API 키, https://www.pexels.com/api 에서 발급)
# 기사에 자체 사진이 없을 때, 헤드라인 키워드로 관련 무료 스톡 이미지를 찾는 데 사용됩니다.
PEXELS_API_KEY = "your_pexels_api_key"

# 4-1) 관련 이미지 검색 (Unsplash Access Key)
# https://unsplash.com/oauth/applications 접속 → 무료 가입 → "New Application" → Access Key 발급
# (API 이용약관상 사용 시 촬영자 크레딧 표기가 필수라 캡션에 자동으로 추가됩니다)
UNSPLASH_ACCESS_KEY = "your_unsplash_access_key"

# 5) Claude API (요약용)
# 환경변수 ANTHROPIC_API_KEY 로 설정하는 것을 권장 (이 파일에 직접 쓰지 마세요)

# 6) 카드 하단에 표시할 본인 인스타그램 계정 (@ 제외하고 아이디만)
INSTAGRAM_HANDLE = "your_instagram_id"

# 7) 클로징 슬라이드(3번째 장)용 브랜드 워드마크 / CTA 문구
BRAND_NAME = "News."
CTA_TAGLINE = "매일 놓치지 않고 소식을 받아보세요."

# 8) 텔레그램 봇 (인물 관련 기사 발견 시 사진 요청 알림용)
# @BotFather에게 /newbot 으로 봇 생성 → Bot Token 발급
# 만든 봇에게 메시지 하나 보낸 뒤 https://api.telegram.org/bot<TOKEN>/getUpdates 접속 → chat id 확인
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_telegram_chat_id"

# 9) 인물기사 사진 답장 타임아웃 (분 단위)
# 이 시간 안에 사진 답장이 없으면 그 기사는 포기하고, 다른 새 기사 처리를 재개합니다.
# (사진을 너무 늦게 보내면 그 동안 다른 뉴스도 아예 처리가 안 멈춰버리는 걸 방지)
PENDING_PHOTO_TIMEOUT_MINUTES = 360  # 예: 360분 = 6시간, 30분으로 하려면 30

# 10) (선택) 게시 직후 자동으로 달 첫 댓글. 비워두면("") 댓글을 달지 않습니다.
# 댓글 기능을 쓰려면 액세스 토큰에 instagram_business_manage_comments 권한이 필요합니다
# (get_access_token.py를 다시 실행해 새 토큰을 발급받고, 앱 대시보드 권한 목록에서도 추가해야 함).
FIRST_COMMENT = ""  # 예: "💬 여러분의 생각은? 댓글로 남겨주세요!"

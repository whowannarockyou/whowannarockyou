# 이 파일을 config.py로 복사한 뒤 실제 값을 채워넣으세요.
# config.py는 .gitignore에 반드시 포함시켜서 깃허브에 올라가지 않게 하세요.

# 1) 뉴스 소스
RSS_FEED_URL = "https://www.yna.co.kr/rss/news.xml"
SOURCE_NAME = "연합뉴스"

# 2) Instagram Graph API
IG_USER_ID = "your_instagram_business_account_id"
IG_ACCESS_TOKEN = "your_long_lived_access_token"

# 3) 이미지 호스팅 (imgbb 무료 API 키, https://api.imgbb.com 에서 발급)
IMGBB_API_KEY = "your_imgbb_api_key"

# 4) 관련 이미지 검색 (Pexels 무료 API 키, https://www.pexels.com/api 에서 발급)
# 기사에 자체 사진이 없을 때, 헤드라인 키워드로 관련 무료 스톡 이미지를 찾는 데 사용됩니다.
PEXELS_API_KEY = "your_pexels_api_key"

# 5) Claude API (요약용)
# 환경변수 ANTHROPIC_API_KEY 로 설정하는 것을 권장 (이 파일에 직접 쓰지 마세요)

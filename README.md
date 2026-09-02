# 인스타 뉴스 자동 게시 봇

RSS → Claude 요약 → 카드뉴스 이미지 → Instagram 자동 게시까지 전 과정을 자동화합니다.

## ⚠️ 시작 전 꼭 확인하세요
- 뉴스 원문/사진을 그대로 재사용하지 않고, **AI 요약 + 출처 명시 + 원문 링크**로 구성했습니다.
  그래도 언론사별 저작권 정책이 다르니, 대량 운영 전 해당 언론사의 뉴스 저작권 이용 정책을 확인하세요.
  (많은 언론사가 '전재' 자체를 금지하고 있어 요약도 상업적 계정에서는 문제될 수 있습니다.)
- Instagram 자동 게시는 **공식 Graph API**로만 진행합니다 (자동 팔로우 같은 비공식 자동화와 다릅니다).

---

## 1단계: Instagram Business/Creator 계정 준비

1. 인스타그램 앱 → 설정 → 계정 → "프로페셔널 계정으로 전환" → **비즈니스** 또는 **크리에이터** 선택
2. 이 계정을 **Facebook 페이지**와 연결 (Graph API는 연결된 FB 페이지를 통해 접근합니다)

## 2단계: Meta 개발자 앱 생성 + 리디렉션 URL 설정 (Instagram 비즈니스 로그인)

이 프로젝트는 Facebook 페이지 연동이 필요 없는 최신 방식인
**"Instagram API with Instagram Login" (Instagram 비즈니스 로그인)** 을 사용합니다.

### 2-1. 리디렉션 URL 먼저 준비하기
"리디렉션 URL"은 로그인 완료 후 사용자가 돌아올 **공개 HTTPS 주소**입니다.
서버 없이 GitHub Pages로 무료로 만들 수 있어요.

1. 이 프로젝트를 GitHub 레포로 push
2. 레포 → Settings → Pages → Source를 `main` 브랜치, 폴더는 `/docs`로 설정 → Save
3. 몇 분 뒤 `https://{당신의 깃헙아이디}.github.io/{레포이름}/` 형태의 URL이 생성됩니다.
   이 주소가 리디렉션 URL입니다. (로컬 테스트만 할 거면 ngrok으로 임시 HTTPS 주소를 만들어도 됩니다.)

### 2-2. Meta 앱 생성 및 리디렉션 URL 등록
1. https://developers.facebook.com/apps 접속 → 로그인 → "앱 만들기"
2. 사용 사례는 **"기타(Other)"**, 앱 유형은 **"비즈니스(Business)"** 선택
3. 앱 대시보드 → "제품 추가" → **Instagram** 추가
4. "API 설정 with Instagram 로그인" → **Business login settings**로 이동
5. **Redirect URI**(리디렉션 URL) 칸에 2-1에서 만든 GitHub Pages 주소를 붙여넣기
6. 필요 시 Deauthorize callback URL / Data deletion request URL도 같은 도메인으로 채우기 (필수 항목인 경우가 많음)
7. 저장 후, 앱 대시보드 → 설정 → 기본 정보에서 **Instagram 앱 ID / 앱 시크릿** 확인

### 2-3. 테스트 계정 등록
앱이 아직 심사(App Review)를 받지 않았다면, 본인의 인스타그램 계정을
"Instagram 테스터"로 등록해야 로그인 테스트가 가능합니다.
앱 대시보드 → 앱 역할 → 역할 → "Instagram 테스터 추가"에서 본인 계정 추가 → 인스타그램 앱에서 초대 수락.

### 2-4. 액세스 토큰 & Instagram User ID 발급
```bash
python get_access_token.py
```
스크립트가 로그인 URL을 출력해줍니다 → 브라우저에서 열고 로그인/승인 →
리디렉트된 GitHub Pages 화면에 뜨는 `code` 값을 복사해서 스크립트에 붙여넣기 →
`IG_USER_ID`와 `IG_ACCESS_TOKEN`(장기, 60일 유효)이 자동 발급됩니다.

권한(scope) 체크리스트: `instagram_business_basic`, `instagram_business_content_publish`

### 2-5. 토큰 만료 관리
- 장기 토큰은 60일 후 만료됩니다. `refresh_token.py`를 30~45일 주기로 실행해 갱신하세요.
- GitHub Actions에 별도 스케줄(예: 매월 1일)로 `refresh_token.py`를 돌리고,
  결과 토큰을 Secrets에 자동 업데이트하는 워크플로우를 추가하면 완전 무인화할 수 있습니다.

## 3단계: 이미지 호스팅 계정 (imgbb) + 관련 이미지 검색 (Pexels)

1. https://api.imgbb.com 접속 → 무료 API 키 발급
2. `config.py`의 `IMGBB_API_KEY`에 입력
3. https://www.pexels.com/api 접속 → 무료 가입 → API 키 발급
4. `config.py`의 `PEXELS_API_KEY`에 입력

> 이 두 가지는 역할이 달라요: **imgbb**는 우리가 만든 카드뉴스 이미지를 인스타그램이
> 읽을 수 있는 공개 URL로 올리는 용도이고, **Pexels**는 기사에 자체 사진이 없을 때
> 헤드라인 키워드로 관련 무료 스톡 이미지를 찾아오는 용도예요.
>
> 운영 규모가 커지면 imgbb 대신 AWS S3나 Cloudinary로 교체하는 걸 권장합니다.
> `post_instagram.py`의 `upload_image()` 함수만 교체하면 됩니다.

## 4단계: Claude API 키 발급

1. https://console.anthropic.com 에서 API 키 발급
2. 환경변수로 설정: `export ANTHROPIC_API_KEY="sk-ant-..."`

## 5단계: 설정 파일 채우기

```bash
cp config.example.py config.py
# config.py를 열어 RSS_FEED_URL, SOURCE_NAME, IG_USER_ID, IG_ACCESS_TOKEN, IMGBB_API_KEY 입력
```

## 6단계: 한글 폰트 준비 (카드뉴스에 필수)

```bash
mkdir -p fonts
# 나눔고딕 등 한글 폰트를 다운로드해서 fonts/ 폴더에 넣기
# 예: NanumGothic.ttf, NanumGothicBold.ttf
```
폰트가 없으면 한글이 깨지거나 렌더링되지 않습니다.

## 7단계: 로컬 테스트

```bash
pip install -r requirements.txt
python main.py
```

정상 동작하면 인스타그램에 카드뉴스 1개가 바로 게시됩니다.

## 8단계: 자동 스케줄링 (GitHub Actions)

1. 이 폴더를 새 GitHub 프라이빗 레포로 push
2. 레포 → Settings → Secrets and variables → Actions에서 아래 Secrets 등록:
   - `RSS_FEED_URL`, `SOURCE_NAME`, `IG_USER_ID`, `IG_ACCESS_TOKEN`, `IMGBB_API_KEY`, `ANTHROPIC_API_KEY`
3. `.github/workflows/post-news.yml`의 cron 시간을 원하는 스케줄로 수정
   (현재는 KST 기준 매일 09:00 / 13:00 / 18:00)
4. push하면 자동으로 스케줄대로 실행됩니다. "Actions" 탭에서 수동 실행(`workflow_dispatch`)도 가능합니다.

---

## 파일 구조
```
insta-news-bot/
├── fetch_news.py         # RSS 수집
├── summarize.py          # Claude로 요약 생성
├── generate_card.py      # 카드뉴스 이미지 생성
├── post_instagram.py     # Instagram Graph API 게시
├── history.py            # 중복 게시 방지
├── main.py               # 전체 파이프라인 실행
├── get_access_token.py   # 최초 1회: 로그인 코드 → 액세스 토큰 발급
├── refresh_token.py      # 60일 만료 전 토큰 갱신
├── docs/
│   └── index.html        # OAuth 리디렉션 URL용 정적 페이지 (GitHub Pages 배포)
├── config.example.py     # 설정 예시 (복사해서 config.py로 사용)
├── requirements.txt
└── .github/workflows/post-news.yml  # 자동 스케줄링
```

## 디자인: 캐러셀(2장) 카드뉴스

토스 스타일(다크 배경 + 볼드 화이트 타이포 + 포인트 컬러)로 디자인되어 있고,
게시물마다 이미지 2장이 캐러셀로 올라갑니다.

- **1번 슬라이드(커버)**: 기사 자체 사진(있으면 자동 삽입) → 없으면 **Pexels에서 헤드라인 키워드로 관련 무료 이미지 자동 검색** → 그마저 없으면 텍스트만 + 핵심 불릿 3개
- **2번 슬라이드(상세)**: 소제목 + 번호 매긴 상세 설명 4개

포인트 컬러는 `generate_card.py` 상단의 `ACCENT = (124, 58, 237)` 값을 바꾸면
전체 디자인의 강조색이 한번에 바뀝니다 (RGB 튜플).

### 한글 폰트 준비 (필수)
`fonts/` 폴더에 아래 두 파일이 필요합니다:
- `NanumGothicExtraBold.ttf` (헤드라인/태그용, 없으면 `NanumGothicBold.ttf`로 자동 대체)
- `NanumGothic.ttf` (본문용)

"나눔고딕 다운로드"로 검색해서 받은 후 `fonts/` 폴더에 넣어주세요. 없으면 카드에 한글이 깨집니다.

## 확장 아이디어
- 언론사 여러 곳 RSS를 리스트로 관리해서 랜덤/순차로 소스 다양화
- 카드뉴스 디자인을 브랜드 톤에 맞게 커스터마이징 (색상, 폰트, 로고 삽입)
- 게시 전 사람이 승인하는 "리뷰 단계" 추가 (Slack 알림 + 승인 버튼 등)
- 액세스 토큰 자동 갱신 로직 추가 (60일 만료 대응)

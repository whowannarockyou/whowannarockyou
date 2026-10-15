"""
스토리 업로드만 따로 테스트하는 스크립트 (피드 게시물은 올리지 않습니다).
사용법: python3 test_story.py            → output/ 폴더에서 가장 최근 cover_*.jpg로 스토리 생성
        python3 test_story.py 이미지경로  → 지정한 이미지(1080x1080 카드)로 스토리 생성
"""
import sys
import glob
import os

import config
from generate_card import generate_story_card
from post_instagram import upload_image, post_story

print("AUTO_STORY 설정값:", getattr(config, "AUTO_STORY", "(config.py에 없음)"))

if len(sys.argv) > 1:
    cover = sys.argv[1]
else:
    files = sorted(glob.glob("output/cover_*.jpg"), key=os.path.getmtime)
    if not files:
        sys.exit("output/ 폴더에 cover_*.jpg가 없습니다. 이미지 경로를 직접 지정해 주세요.")
    cover = files[-1]
print("사용할 커버:", cover)

os.makedirs("output", exist_ok=True)
story_path = "output/story_test.jpg"
generate_story_card(cover, story_path, instagram_handle=config.INSTAGRAM_HANDLE)
print("스토리 이미지 생성 완료:", story_path)

url = upload_image(story_path, config.CLOUDINARY_CLOUD_NAME, config.CLOUDINARY_UPLOAD_PRESET)
print("업로드된 URL:", url)

result = post_story(url, config.IG_USER_ID, config.IG_ACCESS_TOKEN)
print("스토리 게시 성공! id:" , result) if result else print("스토리 게시 실패 (위의 응답 내용을 확인하세요)")

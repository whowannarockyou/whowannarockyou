"""
Instagram Graph API를 이용한 게시 모듈.

** 중요 1 **
Graph API는 로컬 파일을 직접 업로드받지 않고, "공개적으로 접근 가능한 이미지 URL"을 요구합니다.
따라서 이미지를 먼저 어딘가에 호스팅한 뒤 그 URL을 API에 전달해야 합니다.

이 예시는 무료로 빠르게 테스트하기 좋은 imgbb.com API를 이미지 호스팅으로 사용합니다.
운영 단계에서는 AWS S3, Cloudinary, 또는 GitHub Pages(레포에 이미지 커밋 후 raw URL 사용)를
추천합니다. 호스팅 방식만 바꾸면 되도록 upload_image()만 교체하면 됩니다.

** 중요 2 **
get_access_token.py로 발급받은 "Instagram 비즈니스 로그인" 토큰은
graph.facebook.com이 아니라 graph.instagram.com 엔드포인트를 사용합니다.
(Facebook 페이지 연동 방식을 쓴다면 graph.facebook.com으로 바꿔야 합니다.)
"""

import time
import requests


def upload_image(image_path: str, imgbb_api_key: str) -> str:
    """로컬 이미지를 imgbb에 업로드하고 공개 URL을 반환합니다."""
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": imgbb_api_key},
            files={"image": f},
            timeout=30,
        )
    resp.raise_for_status()
    data = resp.json()
    return data["data"]["url"]


def post_to_instagram(
    image_url: str,
    caption: str,
    ig_user_id: str,
    access_token: str,
) -> str:
    """
    Instagram Graph API로 이미지를 게시합니다.
    1) 미디어 컨테이너 생성
    2) 컨테이너 게시(publish)
    반환값: 게시된 미디어 ID
    """
    base_url = f"https://graph.instagram.com/v21.0/{ig_user_id}"

    # 1) 컨테이너 생성
    create_resp = requests.post(
        f"{base_url}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    create_resp.raise_for_status()
    creation_id = create_resp.json()["id"]

    # 처리 대기 (인스타그램 서버가 이미지를 가져와 처리할 시간 필요)
    time.sleep(5)

    # 2) 게시
    publish_resp = requests.post(
        f"{base_url}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    publish_resp.raise_for_status()
    return publish_resp.json()["id"]

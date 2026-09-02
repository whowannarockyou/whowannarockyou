"""
Instagram Graph API를 이용한 게시 모듈. 캐러셀(여러 장) 게시를 지원합니다.

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

GRAPH_BASE = "https://graph.instagram.com/v21.0"


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
    return resp.json()["data"]["url"]


def _create_single_media_container(image_url: str, ig_user_id: str, access_token: str, is_carousel_item: bool = False) -> str:
    data = {"image_url": image_url, "access_token": access_token}
    if is_carousel_item:
        data["is_carousel_item"] = "true"
    resp = requests.post(f"{GRAPH_BASE}/{ig_user_id}/media", data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()["id"]


def post_single_image(image_url: str, caption: str, ig_user_id: str, access_token: str) -> str:
    """이미지 1장짜리 일반 게시물을 올립니다."""
    creation_id = _create_single_media_container(image_url, ig_user_id, access_token)
    time.sleep(5)
    publish_resp = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=30,
    )
    publish_resp.raise_for_status()
    return publish_resp.json()["id"]


def post_carousel(image_urls: list[str], caption: str, ig_user_id: str, access_token: str) -> str:
    """
    이미지 여러 장(2~10장)을 캐러셀로 게시합니다.
    순서: 1) 각 이미지를 carousel item 컨테이너로 생성
          2) 그 item id들을 모아 carousel 컨테이너 생성
          3) 게시(publish)
    """
    if len(image_urls) < 2:
        raise ValueError("캐러셀은 최소 2장 이상의 이미지가 필요합니다. 1장이면 post_single_image를 쓰세요.")

    child_ids = []
    for url in image_urls:
        child_id = _create_single_media_container(url, ig_user_id, access_token, is_carousel_item=True)
        child_ids.append(child_id)
        time.sleep(2)  # 각 아이템 처리 대기

    carousel_resp = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    carousel_resp.raise_for_status()
    creation_id = carousel_resp.json()["id"]

    time.sleep(5)

    publish_resp = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=30,
    )
    publish_resp.raise_for_status()
    return publish_resp.json()["id"]

"""
Instagram Graph API를 이용한 게시 모듈. 캐러셀(여러 장) 게시를 지원합니다.

** 중요 1 **
Graph API는 로컬 파일을 직접 업로드받지 않고, "공개적으로 접근 가능한 이미지 URL"을 요구합니다.
따라서 이미지를 먼저 어딘가에 호스팅한 뒤 그 URL을 API에 전달해야 합니다.

이미지 호스팅은 Cloudinary(무료 티어)를 사용합니다. Unsigned Upload Preset 방식이라
API Secret 없이 Cloud Name + Upload Preset 이름만으로 업로드할 수 있습니다.
※ imgbb, imgur 같은 "이미지 우회 업로드용" 서비스는 짧은 시간에 여러 장을 올리면
   봇 트래픽으로 감지되어 인스타그램이 이후 이미지를 못 가져오는 문제가 있어(400 에러, code 9004)
   원래 이런 용도로 설계된 Cloudinary로 교체했습니다.

** 중요 2 **
get_access_token.py로 발급받은 "Instagram 비즈니스 로그인" 토큰은
graph.facebook.com이 아니라 graph.instagram.com 엔드포인트를 사용합니다.
(Facebook 페이지 연동 방식을 쓴다면 graph.facebook.com으로 바꿔야 합니다.)
"""

import time
import requests

GRAPH_BASE = "https://graph.instagram.com/v21.0"


def upload_image(image_path: str, cloud_name: str, upload_preset: str) -> str:
    """로컬 이미지를 Cloudinary에 업로드하고 공개 URL(secure_url)을 반환합니다."""
    with open(image_path, "rb") as f:
        resp = requests.post(
            f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
            data={"upload_preset": upload_preset},
            files={"file": f},
            timeout=30,
        )
    resp.raise_for_status()
    return resp.json()["secure_url"]



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
        time.sleep(3)  # 각 아이템 업로드 사이 대기 (호스팅 서버 처리 시간 확보)

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

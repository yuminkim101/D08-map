import os
import sys

import requests
from dotenv import load_dotenv

# 🔌 API 주소는 여기 한 곳에만
API = {
    "address": "https://dapi.kakao.com/v2/local/search/address.json",
    "coord2address": "https://dapi.kakao.com/v2/local/geo/coord2address.json",
}

load_dotenv(override=True)


def _kakao_get(url, params):
    """카카오 로컬 API를 불러 documents 목록을 돌려준다. 실패하면 RuntimeError('⛔ ...')."""
    key = os.getenv("KAKAO_REST_API_KEY")
    if not key:
        raise RuntimeError("⛔ .env 에 KAKAO_REST_API_KEY 가 없어요")

    try:
        # 🔌 API 호출
        res = requests.get(
            url,
            headers={"Authorization": f"KakaoAK {key}"},
            params=params,
            timeout=10,
        )
    except requests.RequestException:
        raise RuntimeError("⛔ 카카오에 연결하지 못했어요. 인터넷을 확인해 주세요")

    if res.status_code == 401:
        raise RuntimeError("⛔ 카카오 REST API 키가 틀렸어요")
    if res.status_code == 403:
        raise RuntimeError("⛔ 카카오맵 사용 설정을 켜 주세요")
    if res.status_code != 200:
        raise RuntimeError(f"⛔ 카카오 응답 오류예요 (코드 {res.status_code})")

    return res.json().get("documents", [])


def address_to_coord(address):
    """주소를 (위도, 경도)로 바꾼다. 못 찾으면 None. 실패하면 RuntimeError('⛔ ...')."""
    docs = _kakao_get(API["address"], {"query": address})
    if not docs:
        return None

    # x = 경도, y = 위도 (글자로 옴)
    위도, 경도 = float(docs[0]["y"]), float(docs[0]["x"])
    if not (33 <= 위도 <= 39 and 124 <= 경도 <= 132):
        return None
    return 위도, 경도


def coord_to_address(위도, 경도):
    """(위도, 경도)를 도로명 주소로 바꾼다. 도로명이 없으면 지번 주소. 못 찾으면 None."""
    if not (33 <= 위도 <= 39 and 124 <= 경도 <= 132):
        return None

    # 요청은 x=경도, y=위도
    docs = _kakao_get(API["coord2address"], {"x": 경도, "y": 위도})
    if not docs:
        return None

    road = docs[0].get("road_address")  # 비어 있을 수 있음(null)
    if road:
        return road["address_name"]
    jibun = docs[0].get("address")
    return jibun["address_name"] if jibun else None


if __name__ == "__main__":
    address = input("주소 (예: 서울특별시 성동구 왕십리로 83-21): ").strip()
    if not address:
        sys.exit("주소를 입력해 주세요")

    try:
        coord = address_to_coord(address)
        if coord is None:
            sys.exit(f"'{address}'을(를) 찾지 못했어요")
        위도, 경도 = coord
        print(f"1) 주소 → 좌표: 위도 {위도}, 경도 {경도}")

        back = coord_to_address(위도, 경도)
    except RuntimeError as e:
        sys.exit(str(e))

    if back is None:
        sys.exit("이 좌표의 주소를 찾지 못했어요")
    print(f"2) 좌표 → 주소: {back}")
    print("\n출처: 카카오 로컬 API (주소로 좌표 변환, 좌표로 주소 변환)")

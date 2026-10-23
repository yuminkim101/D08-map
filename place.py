import os
import sys

import requests
from dotenv import load_dotenv

# 🔌 API 주소는 여기 한 곳에만
API = {
    "keyword": "https://dapi.kakao.com/v2/local/search/keyword.json",
}

load_dotenv(override=True)


def search_place(query, size=5):
    """키워드로 장소를 찾아 [{이름, 주소, 위도, 경도}, ...] 로 돌려준다. 실패하면 RuntimeError('⛔ ...')."""
    key = os.getenv("KAKAO_REST_API_KEY")
    if not key:
        raise RuntimeError("⛔ .env 에 KAKAO_REST_API_KEY 가 없어요")

    try:
        # 🔌 API 호출
        res = requests.get(
            API["keyword"],
            headers={"Authorization": f"KakaoAK {key}"},
            params={"query": query, "size": size},
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

    places = []
    for doc in res.json().get("documents", []):
        # x = 경도, y = 위도 (글자로 옴)
        위도, 경도 = float(doc["y"]), float(doc["x"])
        if not (33 <= 위도 <= 39 and 124 <= 경도 <= 132):
            continue
        places.append({
            "이름": doc["place_name"],
            "주소": doc.get("road_address_name") or doc["address_name"],
            "위도": 위도,
            "경도": 경도,
        })
    return places


if __name__ == "__main__":
    query = input("검색어 (예: 성수동 카페): ").strip()
    if not query:
        sys.exit("검색어를 입력해 주세요")

    try:
        places = search_place(query)
    except RuntimeError as e:
        sys.exit(str(e))

    if not places:
        sys.exit(f"'{query}'을(를) 찾지 못했어요")

    for p in places:
        print(f"{p['이름']} | {p['주소']} | 위도 {p['위도']} | 경도 {p['경도']}")
    print("\n출처: 카카오 로컬 API (키워드로 장소 검색)")

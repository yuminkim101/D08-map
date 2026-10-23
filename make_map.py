import html
import json
import os
import sys

from dotenv import load_dotenv

from place import search_place

# 🔌 API 주소는 여기 한 곳에만 (지도 그림은 브라우저가 JS 키로 불러온다)
API = {
    "sdk": "https://dapi.kakao.com/v2/maps/sdk.js",
}

load_dotenv(override=True)

MAX_MARKERS = 200

TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
  body { font-family: sans-serif; margin: 16px; }
  #map { width: 100%; height: 500px; }
  .tip { color: #555; font-size: 14px; margin-top: 8px; }
  .info { padding: 8px 10px; font-size: 13px; line-height: 1.5; min-width: 180px; }
  .info .name { font-weight: bold; }
</style>
</head>
<body>
<h3>__TITLE__</h3>
<div id="map"></div>
__TIP__
<script src="__SDK__"></script>
<script>
const places = __PLACES__;

kakao.maps.load(function () {
  const map = new kakao.maps.Map(document.getElementById("map"), {
    center: new kakao.maps.LatLng(places[0].위도, places[0].경도),
    level: 4,
  });
  const bounds = new kakao.maps.LatLngBounds();
  let openInfo = null;

  places.forEach(function (p) {
    // 순서 주의: LatLng(위도, 경도)
    const pos = new kakao.maps.LatLng(p.위도, p.경도);
    const marker = new kakao.maps.Marker({ map: map, position: pos });
    bounds.extend(pos);

    // 이름·주소는 textContent로 넣는다 (따옴표·태그가 있어도 안 깨짐)
    const box = document.createElement("div");
    box.className = "info";
    const name = document.createElement("div");
    name.className = "name";
    name.textContent = p.이름;
    const addr = document.createElement("div");
    addr.textContent = p.주소;
    box.appendChild(name);
    box.appendChild(addr);
    const info = new kakao.maps.InfoWindow({ content: box, removable: true });

    kakao.maps.event.addListener(marker, "click", function () {
      if (openInfo) openInfo.close();
      info.open(map, marker);
      openInfo = info;
    });
  });

  if (places.length > 1) {
    map.setBounds(bounds);  // 마커가 전부 화면 안에 들어오게
  }
});
</script>
</body>
</html>
"""


TIP = '<p class="tip">지도가 회색이면: ① 카카오맵 사용 설정 ② 지금 주소(포트까지) 등록 ③ 서버 주소로 열기</p>'


def kakao_map_html(places, title="장소 지도", tip=True):
    """[{이름, 주소, 위도, 경도}, ...] 를 카카오 지도 마커로 찍은 HTML 글자를 돌려준다.

    JS 키(KAKAO_JS_KEY)만 쓴다. REST 키는 HTML에 넣지 않는다.
    tip=True 면 지도 아래에 '지도가 회색이면' 안내 한 줄을 넣는다(수업·개발용 기본값).
    실패하면 RuntimeError('⛔ ...').
    """
    js_key = os.getenv("KAKAO_JS_KEY")
    if not js_key:
        raise RuntimeError("⛔ .env 에 KAKAO_JS_KEY 가 없어요")
    if js_key == os.getenv("KAKAO_REST_API_KEY"):
        raise RuntimeError("⛔ KAKAO_JS_KEY 에 REST 키가 들어 있어요. JavaScript 키를 넣어 주세요")

    places = places[:MAX_MARKERS]
    if not places:
        raise RuntimeError("⛔ 지도에 찍을 장소가 없어요")

    # json.dumps 로 데이터를 넣고, </script> 로 오해되지 않게 "</" 를 막는다
    data = json.dumps(places, ensure_ascii=False).replace("</", "<\\/")
    sdk = f"{API['sdk']}?appkey={js_key}&autoload=false"

    return (
        TEMPLATE.replace("__TITLE__", html.escape(title))
        .replace("__TIP__", TIP if tip else "")
        .replace("__SDK__", sdk)
        .replace("__PLACES__", data)
    )


def kakao_map(places, path="map.html", title="장소 지도", tip=True):
    """kakao_map_html() 결과를 HTML 파일로 저장하고 파일 경로를 돌려준다."""
    page = kakao_map_html(places, title=title, tip=tip)
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


if __name__ == "__main__":
    query = input("검색어 (예: 성수동 카페): ").strip()
    if not query:
        sys.exit("검색어를 입력해 주세요")

    try:
        places = search_place(query, size=10)
        if not places:
            sys.exit(f"'{query}'을(를) 찾지 못했어요")
        path = kakao_map(places, "map.html", title=f"{query} 검색 결과")
    except RuntimeError as e:
        sys.exit(str(e))

    print(f"{len(places)}곳을 {path} 에 만들었어요.")
    print("\n열기:")
    print("  1) 이 폴더에서  python -m http.server 8000 --bind 127.0.0.1")
    print("  2) 브라우저에서  http://localhost:8000/map.html")
    print("  (카카오 콘솔 JavaScript SDK 도메인에 http://localhost:8000 이 등록돼 있어야 해요)")
    print("\n출처: 카카오 로컬 API (키워드로 장소 검색), 카카오 지도 JavaScript SDK")

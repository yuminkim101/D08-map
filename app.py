import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from make_map import kakao_map_html
from place import search_place

load_dotenv(override=True)

st.set_page_config(page_title="장소를 찾아드려요", layout="wide")


@st.cache_data(ttl=600)
def cached_search(query, size):
    # 에러는 캐시하지 않는다: 예외를 내면 캐시에 저장되지 않고, 밖에서 받아 화면에 보여 준다
    return search_place(query, size=size)


st.title("장소를 찾아드려요")

with st.form("search"):
    col1, col2 = st.columns([4, 1])
    query = col1.text_input("검색어", value="성수동 카페", placeholder="예: 강남역 약국")
    size = col2.slider("몇 개를 찾아드릴까요?", 1, 15, 10)
    submitted = st.form_submit_button("검색")

query = query.strip()
if not query:
    st.error("검색어를 입력해 주세요")
    st.stop()

try:
    places = cached_search(query, size)
except RuntimeError as e:
    st.error(str(e).removeprefix("⛔ "))
    st.stop()

if not places:
    st.error(f"'{query}'을(를) 찾지 못했어요")
    st.stop()

try:
    page = kakao_map_html(places, title=f"{query} 검색 결과", tip=False)
except RuntimeError as e:
    st.error(str(e).removeprefix("⛔ "))
    st.stop()

st.iframe(page, height=620)
st.dataframe(pd.DataFrame(places), hide_index=True, width="stretch")

st.caption("출처: 카카오 로컬 API (키워드로 장소 검색), 카카오 지도 JavaScript SDK")

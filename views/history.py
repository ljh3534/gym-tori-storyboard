import streamlit as st

from notion_archive import list_storyboards, get_storyboard_content

st.title("콘티 목록")
st.caption("지금까지 생성한 콘티들이에요. 접었다 펴서 내용을 확인할 수 있어요.")

if st.button("새로고침"):
    st.cache_data.clear()


@st.cache_data(ttl=60)
def _cached_list():
    return list_storyboards()


try:
    items = _cached_list()
except Exception as e:
    st.error(f"목록을 불러오지 못했어요: {e}")
    st.stop()

if not items:
    st.info("아직 생성된 콘티가 없어요. '새 콘티 만들기' 탭에서 먼저 하나 만들어보세요.")
    st.stop()

for item in items:
    label = f"{item['title']}  ·  {item['created']}"
    with st.expander(label):
        st.write(f"원본 링크: {item['source_url']}")
        st.write(f"[노션에서 열기]({item['notion_url']})")
        if st.button("본문 불러오기", key=f"load_{item['page_id']}"):
            with st.spinner("불러오는 중..."):
                content = get_storyboard_content(item["page_id"])
            st.markdown("---")
            st.markdown(content)
            st.download_button(
                "콘티 다운로드 (.md)",
                content,
                file_name="storyboard.md",
                key=f"dl_{item['page_id']}",
            )

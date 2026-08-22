import streamlit as st

from transcript import get_source_material
from storyboard import generate_storyboard
from notion_archive import save_storyboard

st.title("gym.tori 콘티 생성기")
st.caption("유튜브 링크를 넣으면 자막(없으면 제목+댓글)을 기반으로 콘티 초안을 만들어줍니다.")

url = st.text_input("유튜브 링크")
format_choice = st.radio("어떤 포맷으로 만들까요?", ["릴스", "캐러셀"], horizontal=True)

if st.button("콘티 생성", type="primary", disabled=not url):
    with st.spinner("영상 정보를 가져오는 중..."):
        try:
            material = get_source_material(url)
        except Exception as e:
            st.error(f"영상 정보를 가져오지 못했어요: {e}")
            st.stop()

    st.subheader(material["title"])
    if material["used_fallback"]:
        st.info("자막이 없는 영상이라 제목+댓글로 대체했어요. 콘티 품질이 자막 있는 경우보다 낮을 수 있어요.")
    else:
        st.success("자막을 찾아서 사용했어요.")

    with st.spinner(f"{format_choice} 콘티 작성 중... (초안 생성 + 검수 2단계라 1~2분 정도 걸려요)"):
        try:
            storyboard = generate_storyboard(
                title=material["title"],
                transcript=material["transcript"],
                comments=material["comments"],
                format_choice=format_choice,
            )
        except Exception as e:
            st.error(f"콘티 생성에 실패했어요: {e}")
            st.stop()

    st.markdown("---")
    st.markdown(storyboard)
    st.download_button("콘티 다운로드 (.md)", storyboard, file_name="storyboard.md")

    try:
        save_storyboard(material["title"], format_choice, url, storyboard)
        st.success("'콘티 목록' 탭에 저장했어요. 창을 닫아도 다시 볼 수 있어요.")
    except Exception as e:
        st.warning(f"콘티는 만들어졌지만 저장에는 실패했어요: {e}")

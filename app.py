import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# 로컬에서는 .env가 이미 채워주고, Streamlit Cloud에서는 대시보드에 등록한
# Secrets가 여기로 들어오니 환경변수로 옮겨준다 (다른 모듈은 os.environ만 봄).
for _key in ("YOUTUBE_API_KEY", "ANTHROPIC_API_KEY", "NOTION_API_KEY", "NOTION_STORYBOARD_DB_ID"):
    if _key not in os.environ and _key in st.secrets:
        os.environ[_key] = st.secrets[_key]

st.set_page_config(page_title="gym.tori 콘티 생성기", page_icon="🏋️")

pages = [
    st.Page("views/generate.py", title="새 콘티 만들기", icon="✍️"),
    st.Page("views/history.py", title="콘티 목록", icon="📋"),
]
st.navigation(pages).run()

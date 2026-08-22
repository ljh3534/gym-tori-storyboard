"""생성된 콘티를 노션에 저장하고, 목록/본문을 다시 불러온다.

Streamlit Cloud는 배포될 때마다 로컬 디스크가 초기화되기 때문에,
콘티 히스토리는 노션 DB(gym.tori 콘티 아카이브)에 저장해서 영속시킨다.
"""

import os
from datetime import date

from notion_client import Client

MAX_BLOCK_CHARS = 1900  # 노션 rich_text 블록당 2000자 제한, 여유 두고 자름
MAX_CHILDREN_PER_CALL = 100  # 노션 API: 페이지 생성 시 children 최대 100개


def _client() -> Client:
    return Client(auth=os.environ["NOTION_API_KEY"])


def _data_source_id() -> str:
    return os.environ["NOTION_STORYBOARD_DB_ID"]


def _markdown_to_blocks(markdown: str) -> list[dict]:
    """마크다운을 노션 문단 블록으로 단순 변환 (서식은 버리고 텍스트만 보존)."""
    blocks = []
    for para in markdown.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        for i in range(0, len(para), MAX_BLOCK_CHARS):
            chunk = para[i:i + MAX_BLOCK_CHARS]
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]},
            })
    return blocks[:MAX_CHILDREN_PER_CALL]


def save_storyboard(title: str, format_choice: str, source_url: str, storyboard_md: str) -> str:
    """콘티를 노션에 새 페이지로 저장하고 페이지 URL을 반환한다."""
    client = _client()
    page = client.pages.create(
        parent={"type": "data_source_id", "data_source_id": _data_source_id()},
        properties={
            "제목": {"title": [{"text": {"content": f"[{format_choice}] {title}"}}]},
            "포맷": {"select": {"name": format_choice}},
            "원본 링크": {"url": source_url},
            "생성일": {"date": {"start": date.today().isoformat()}},
        },
        children=_markdown_to_blocks(storyboard_md),
    )
    return page["url"]


def list_storyboards(limit: int = 50) -> list[dict]:
    """최근 생성된 콘티 목록 (제목/포맷/원본링크/생성일/page_id)을 최신순으로."""
    client = _client()
    resp = client.data_sources.query(
        data_source_id=_data_source_id(),
        sorts=[{"property": "생성일", "direction": "descending"}],
        page_size=limit,
    )
    items = []
    for page in resp["results"]:
        props = page["properties"]
        title_blocks = props["제목"]["title"]
        fmt = props["포맷"]["select"]
        source = props["원본 링크"]
        created = props["생성일"]["date"]
        items.append({
            "page_id": page["id"],
            "notion_url": page["url"],
            "title": title_blocks[0]["text"]["content"] if title_blocks else "(제목 없음)",
            "format": fmt["name"] if fmt else "",
            "source_url": source["url"] if source else "",
            "created": created["start"] if created else "",
        })
    return items


def get_storyboard_content(page_id: str) -> str:
    """페이지 본문(문단 블록들)을 이어붙여서 마크다운처럼 복원."""
    client = _client()
    blocks = client.blocks.children.list(block_id=page_id, page_size=100)
    parts = []
    for block in blocks["results"]:
        if block["type"] == "paragraph":
            text = "".join(t["plain_text"] for t in block["paragraph"]["rich_text"])
            parts.append(text)
    return "\n\n".join(parts)

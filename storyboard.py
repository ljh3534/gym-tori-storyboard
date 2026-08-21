"""수집한 원재료 + gym.tori 스타일 가이드로 콘티를 생성한다."""

import os
from pathlib import Path

from anthropic import Anthropic

MODEL = "claude-opus-5"

STYLE_GUIDE_PATH = Path(__file__).parent.parent / "인스타툰" / "gym.tori_릴스기획_참고문서.md"

PROMPT_TEMPLATE = """당신은 gym.tori 인스타그램 계정의 콘티 작가입니다.
아래 "스타일 가이드"를 반드시 따라서, 주어진 유튜브 영상 소재로 {format_label} 콘티를 짜세요.

# 스타일 가이드
{style_guide}

# 소재
제목: {title}
{material_label}: {material}

# 요청
- {format_instruction}
- 실명, 특정 브랜드명, 특정 가능한 디테일(동네·학교 등)은 재창작해서 익명화할 것
- 원본의 구체적 수치(조회수, 금액 등)를 그대로 베끼지 말고 각색할 것
- 출력은 마크다운으로, 컷/슬라이드별로 번호를 매겨서 화면 설명과 대사·자막을 구분해서 작성할 것
"""

REELS_INSTRUCTION = (
    "릴스 콘티: 14~20컷 내외, '썰 푸는' 회고형 내레이션 톤. "
    "썸네일(후킹) → 본문(전개) → CTA(팔로우/댓글 유도) 구조를 지킬 것. "
    "캐릭터는 얼굴 없는 블롭 마스터 캐릭터 기준으로 장면을 구성할 것 (스타일 가이드 4번 참고)"
)

CAROUSEL_INSTRUCTION = (
    "캐러셀(카드뉴스) 콘티: 8~10장 슬라이드. "
    "표지(후킹 문구) → 본문(정보/리스트/비교, 슬라이드당 핵심 1개) → 마무리(요약+CTA) 구조로 구성할 것. "
    "서사보다 정보 밀도를 우선하고, 의학적으로 단정하는 문구는 피하고 필요하면 '~일 수 있음' 톤을 쓸 것"
)


def _load_style_guide() -> str:
    if STYLE_GUIDE_PATH.exists():
        return STYLE_GUIDE_PATH.read_text(encoding="utf-8")
    return "(스타일 가이드 파일을 못 찾았어요. 기본 톤: 얼굴 없는 블롭 캐릭터, 회고형 '썰' 톤)"


def generate_storyboard(title: str, transcript: str | None, comments: list[str], format_choice: str) -> str:
    """format_choice: '릴스' 또는 '캐러셀'"""
    if transcript:
        material_label = "자막 전문"
        material = transcript
    else:
        material_label = "댓글 (자막 없어서 대체 자료로 사용)"
        material = "\n".join(f"- {c}" for c in comments) or "(댓글도 없어서 제목만으로 진행)"

    instruction = REELS_INSTRUCTION if format_choice == "릴스" else CAROUSEL_INSTRUCTION

    prompt = PROMPT_TEMPLATE.format(
        format_label=format_choice,
        style_guide=_load_style_guide(),
        title=title,
        material_label=material_label,
        material=material,
        format_instruction=instruction,
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        output_config={"effort": "high"},
        messages=[{"role": "user", "content": prompt}],
    )

    return "".join(b.text for b in resp.content if b.type == "text")

"""수집한 원재료 + gym.tori 스타일 가이드로 콘티를 생성한다."""

import os
from pathlib import Path

from anthropic import Anthropic

MODEL = "claude-opus-5"

# 로컬(준호 PC)에서는 항상 최신인 원본 문서를 우선 사용하고,
# 클라우드 배포본에는 그 폴더가 없으니 저장소에 포함된 사본(style_guide.md)으로 대체한다.
STYLE_GUIDE_CANDIDATES = [
    Path(__file__).parent.parent / "인스타툰" / "gym.tori_릴스기획_참고문서.md",
    Path(__file__).parent / "style_guide.md",
]

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

# 계정 현재 상황(팔로워 규모·알고리즘 노출) 기준으로 Meta AI에 문의해서 받은 권장 분량.
# 나중에 계정 성장하면서 권장치가 바뀌면 이 값들만 수정하면 됨.
REELS_MAX_CUTS = 10
REELS_DURATION = "18~25초 (최대 30초를 넘기지 않음)"
CAROUSEL_SLIDE_COUNT = 8

REELS_INSTRUCTION = (
    f"릴스 콘티: 최대 {REELS_MAX_CUTS}컷 이내, 완성 영상 기준 {REELS_DURATION} 분량으로 압축할 것 "
    "(컷당 대략 2~3초로 배분한다고 가정하고 전개를 그 안에 욱여넣지 말고 애초에 컷 수부터 그 범위로 설계할 것). "
    "'썰 푸는' 회고형 내레이션 톤. "
    "썸네일(후킹) → 본문(전개) → CTA(팔로우/댓글 유도) 구조를 지킬 것. "
    "캐릭터는 얼굴 없는 블롭 마스터 캐릭터 기준으로 장면을 구성할 것 (스타일 가이드 4번 참고)"
)

CAROUSEL_COVER_STYLE = (
    "1번 슬라이드(표지)는 벤치마킹 계정 @kkunoping.health 스타일을 참고해서 아래 네 가지를 반드시 포함할 것: "
    "① 굵은 헤드라인 카피 2~3줄 — 통념 깨기형(예: '꾸준함에 대한 착각') 또는 숫자·경험 후킹형(예: '6년 동안 헬스 했더니 생긴 충격적인 일') 중 하나로 "
    "② 그 상황에 맞는 표정·포즈로 반응하는 캐릭터 삽화 설명 "
    "③ 캐릭터 옆에 짧은 말풍선 한 줄 — 헤드라인에 공감하거나 되묻는 톤(예: '이렇게 쉬웠는데 난 몰랐어..?', '식단하는데 왜?') "
    "④ 전 슬라이드에 걸쳐 배경색을 통일해서 브랜드 각인이 되게 할 것(색상은 스타일 가이드에 맞게 자유롭게 정하되 일관되게)"
)

CAROUSEL_INSTRUCTION = (
    f"캐러셀(카드뉴스) 콘티: 정확히 {CAROUSEL_SLIDE_COUNT}장 슬라이드로 구성할 것 (더 많지도 적지도 않게). "
    f"{CAROUSEL_COVER_STYLE} "
    "2번 슬라이드부터는 본문(정보/리스트/비교, 슬라이드당 핵심 1개) → 마무리(요약+CTA) 구조로 구성할 것. "
    "서사보다 정보 밀도를 우선하고, 의학적으로 단정하는 문구는 피하고 필요하면 '~일 수 있음' 톤을 쓸 것"
)


def _load_style_guide() -> str:
    for path in STYLE_GUIDE_CANDIDATES:
        if path.exists():
            return path.read_text(encoding="utf-8")
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

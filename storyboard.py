"""수집한 원재료 + gym.tori 스타일 가이드·생성 원칙으로 콘티를 생성하고 검수한다.

2단계 파이프라인: (1) 초안 생성 → (2) "정보는 캐릭터가 연기한다" 원칙 기준으로 검수·재작성.
카드뉴스식으로 새는 걸 원천 차단하려고 검수 단계를 별도 API 호출로 분리했다 (generation_principles.md 4번).
"""

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

PRINCIPLES_PATH = Path(__file__).parent / "generation_principles.md"

# 계정 현재 상황(팔로워 규모·알고리즘 노출) 기준으로 Meta AI에 문의해서 받은 권장 분량.
# generation_principles.md의 릴스 규칙(14~20컷)보다 이 값이 우선한다 — 더 최신 기준값.
REELS_MAX_CUTS = 10
REELS_DURATION = "18~25초 (최대 30초를 넘기지 않음)"
CAROUSEL_SLIDE_COUNT = 8

DRAFT_PROMPT_TEMPLATE = """당신은 gym.tori 인스타그램 계정의 콘티 작가입니다.
아래 "스타일 가이드"와 "생성 원칙"을 반드시 따라서, 주어진 유튜브 영상 소재로 {format_label} 콘티를 짜세요.

# 스타일 가이드
{style_guide}

# 생성 원칙
{principles}

# 소재
제목: {title}
{material_label}: {material}

# 작업 순서
1. 소재에서 핵심 갈등/정보/반전 포인트를 뽑는다
2. 특정 가능한 디테일(인물·장소·고유 수치)을 각색한다
3. 정보 전달이 필요한 소재라도 카드로 나열하지 말고, 짐토리(또는 조연)가 그 정보를 직접 겪거나 알아가는 서사로 감싼다 — "생성 원칙" 1번을 모든 컷/슬라이드에 적용한다
4. {format_instruction}
5. 마지막에 제작 메모(신규 필요 에셋, 각색 처리 내역)와 캡션 초안을 덧붙인다

# 출력 형식
- 마크다운, 컷/슬라이드별로 번호를 매길 것
- 각 컷/슬라이드마다 [화면 설명 / 자막{bubble_field} / 하단 미니카피]를 구분해서 작성할 것
"""

REVIEW_PROMPT_TEMPLATE = """당신은 gym.tori 콘티 감수자입니다.
아래 "생성 원칙"의 1번 원칙("정보는 캐릭터가 연기한다")과 self-check 기준으로 초안 콘티를 검수하세요.

# 생성 원칙
{principles}

# 검수 대상 초안
{draft}

# 요청
- 컷/슬라이드 하나하나를 self-check 3문항에 비추어 확인할 것
  (메인 비주얼이 캐릭터가 아니라 표/카드/도식인가 / 텍스트 존과 캐릭터 존이 분리돼 있는가 / 캐릭터가 정보를 보고 반응만 하는가)
- 셋 중 하나라도 해당하면 그 컷/슬라이드만 원칙에 맞게 다시 쓸 것 (캐릭터가 정보를 직접 연기하는 구도로)
- 문제 없는 컷/슬라이드는 그대로 유지할 것
- 최종 결과물만, 초안과 완전히 동일한 섹션 구성으로 출력할 것 (초안에 있던 제작 메모·캡션 초안 섹션은 그대로 유지)
- "감수했습니다", "이 부분을 수정했습니다" 같은 감수 과정 설명이나 별도의 수정 내역 메모는 절대 추가하지 말 것 — 검수 후 최종 콘티 그 자체만 출력
"""

REELS_INSTRUCTION = (
    f"릴스 콘티: 최대 {REELS_MAX_CUTS}컷 이내, 완성 영상 기준 {REELS_DURATION} 분량으로 압축할 것 "
    "(컷당 대략 2~3초로 배분한다고 가정하고 전개를 그 안에 욱여넣지 말고 애초에 컷 수부터 그 범위로 설계할 것). "
    "말풍선·직접 대사 인용은 쓰지 말고, 네이트판 썰 스타일 반말 종결어미('~있었음', '~던거임')로 서술할 것 — 대사는 서술 안에 녹일 것. "
    "썸네일+컷1은 훅 유닛(임팩트 위주, 시간순 무관), 컷2부터 실제 이야기가 시작되는 구조로 할 것. "
    "컷 타이밍: 액션·펀치라인 2초 / 일반 3초 / 텍스트 많은 컷·해소 컷 4~5초. "
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
    "텍스트 위주 카드뉴스는 절대 금지 — 표지뿐 아니라 본문 슬라이드도 전부 짐토리(또는 조연)가 등장해서 정보를 직접 연기하는 구도로 만들 것. "
    f"{CAROUSEL_COVER_STYLE} "
    "2번 슬라이드부터는 본문(정보/리스트/비교, 슬라이드당 핵심 1개를 캐릭터 행동으로 표현) → 마무리(요약+CTA, 캐릭터의 자기고백형 리액션으로) 구조로 구성할 것. "
    "의학적으로 단정하는 문구는 피하고 필요하면 '~일 수 있음' 톤을 쓸 것"
)


def _load_style_guide() -> str:
    for path in STYLE_GUIDE_CANDIDATES:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return "(스타일 가이드 파일을 못 찾았어요. 기본 톤: 얼굴 없는 블롭 캐릭터, 회고형 '썰' 톤)"


def _load_principles() -> str:
    if PRINCIPLES_PATH.exists():
        return PRINCIPLES_PATH.read_text(encoding="utf-8")
    return "(생성 원칙 파일을 못 찾았어요. 기본 원칙: 정보는 항상 캐릭터의 행동·표정·대사로 전달하고, 캐릭터 밖에 뜨는 카드·표·도식을 메인 비주얼로 쓰지 말 것)"


def _call_claude(prompt: str) -> str:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "high"},
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def _generate_draft(title: str, transcript: str | None, comments: list[str], format_choice: str) -> str:
    if transcript:
        material_label = "자막 전문"
        material = transcript
    else:
        material_label = "댓글 (자막 없어서 대체 자료로 사용)"
        material = "\n".join(f"- {c}" for c in comments) or "(댓글도 없어서 제목만으로 진행)"

    instruction = REELS_INSTRUCTION if format_choice == "릴스" else CAROUSEL_INSTRUCTION
    bubble_field = " / 말풍선" if format_choice == "캐러셀" else ""

    prompt = DRAFT_PROMPT_TEMPLATE.format(
        format_label=format_choice,
        style_guide=_load_style_guide(),
        principles=_load_principles(),
        title=title,
        material_label=material_label,
        material=material,
        format_instruction=instruction,
        bubble_field=bubble_field,
    )
    return _call_claude(prompt)


def _review_and_fix(draft: str) -> str:
    prompt = REVIEW_PROMPT_TEMPLATE.format(
        principles=_load_principles(),
        draft=draft,
    )
    return _call_claude(prompt)


def generate_storyboard(title: str, transcript: str | None, comments: list[str], format_choice: str) -> str:
    """format_choice: '릴스' 또는 '캐러셀'. 초안 생성 후 원칙 기준으로 한 번 더 검수해서 최종본을 돌려준다."""
    draft = _generate_draft(title, transcript, comments, format_choice)
    return _review_and_fix(draft)

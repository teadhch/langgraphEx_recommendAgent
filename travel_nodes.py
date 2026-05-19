# ─────────────────────────────────────────────────────────────
# step04_travel_nodes.py
# 여행 계획 그래프에서 사용할 Node 함수 7개를 구현하는 예제
# ─────────────────────────────────────────────────────────────
"""
이 파일에서는 실제 여행 계획 파이프라인에 필요한 Node들을 만듭니다.
전체 Node 흐름:
1. analyze_input          : 입력값 검증
2. recommend_destination  : 목적지 추천
3-A. plan_overseas        : 해외 여행 일정 수립
3-B. plan_domestic        : 국내 여행 일정 수립
4. recommend_hotels       : 숙소 추천
5. plan_budget            : 예산 배분
6. create_summary         : 최종 보고서 작성
각 Node는 다음 규칙을 따릅니다.
- state를 입력으로 받습니다.
- 필요한 값만 state에서 읽습니다.
- 자신이 업데이트할 필드만 dict로 반환합니다.
"""
from typing import TypedDict, Annotated
import operator
class TravelState(TypedDict):
    """
    여행 계획 그래프 전체가 공유하는 State 구조입니다.
    """
    # 사용자 입력
    budget: int
    days: int
    # 실행 중 생성되는 데이터
    destination: str
    is_overseas: bool
    itinerary: list
    hotels: list
    budget_plan: dict
    summary: str
    # 실행 로그
    # 여러 Node가 messages를 반환할 때 기존 리스트에 이어붙입니다.
    messages: Annotated[list, operator.add]

# ─────────────────────────────────────────────────────────────
# Node 1. 입력 검증
# ─────────────────────────────────────────────────────────────

def analyze_input(state: TravelState) -> dict:

    """
    입력값을 검증하고 분석 시작 로그를 남기는 Node입니다.
    검사 내용:
    ----------

    1. 예산은 최소 50만원 이상이어야 합니다.

    2. 여행 박 수는 1 이상 30 이하이어야 합니다.

    문제가 있으면:

    -----------

    ValueError를 발생시켜 그래프 실행을 중단합니다.

    문제가 없으면:

    -----------

    messages에 분석 시작 로그를 추가합니다.

    """

    # State에서 budget과 days를 읽습니다.

    budget = state["budget"]

    days = state["days"]

    # 예산이 너무 적은 경우

    if budget < 50:

        raise ValueError(f"예산 오류: {budget}만원 (최소 50만원)")

    # 여행 일수가 허용 범위를 벗어난 경우

    if not (1 <= days <= 30):

        raise ValueError(f"일수 오류: {days}일 (1~30일 사이)")

    # 입력값이 정상이라면 로그를 남깁니다.

    return {
        "messages": [
            f"✈️ 분석 시작: {days}박 {days + 1}일, 예산 {budget}만원"
        ]

    }

# ─────────────────────────────────────────────────────────────

# Node 2. 목적지 추천

# ─────────────────────────────────────────────────────────────

def recommend_destination(state: TravelState) -> dict:

    """
    예산과 여행 일수에 따라 목적지를 추천하는 Node입니다.
    이 Node가 중요한 이유:
    --------------------
    이 Node에서 결정한 is_overseas 값이
    다음 조건부 분기의 기준이 됩니다.
    반환하는 값:
    ----------
    - destination
    - is_overseas
    - essages
    """

    budget = state["budget"]
    days = state["days"]

    # 예산과 일수 기준으로 목적지를 결정합니다.
    if budget >= 300 and days >= 5:
        dest = "일본 도쿄"
        overseas = True

    elif budget >= 200 and days >= 3:
        dest = "태국 방콕"
        overseas = True

    elif budget >= 150:
        dest = "국내 제주도"
        overseas = False

    else:
        dest = "국내 부산"
        overseas = False

    return {
        # 추천 목적지
        "destination": dest,
        # 해외 여부
        # 이 값은 route_by_destination 함수에서 사용됩니다.
        "is_overseas": overseas,
        # 처리 로그
        "messages": [
            f"🧭 목적지: {dest} ({'해외' if overseas else '국내'})"
        ],
    }

# ─────────────────────────────────────────────────────────────
# Node 3-A. 해외 일정 수립
# ─────────────────────────────────────────────────────────────
def plan_overseas(state: TravelState) -> dict:
    """
    해외 여행 전용 일정을 만드는 Node입니다.
    실행 조건:
    ----------
    recommend_destination 이후
    is_overseas가 True이면 이 Node가 실행됩니다.
    포함 내용:
    ----------
    - 인천 출발
    - 공항에서 호텔 이동
    - 문화 탐방
    - 쇼핑 및 맛집 투어
    - 귀국 일정
    - 비자/환전 안내 메시지
    """

    dest = state["destination"]
    days = state["days"]

    # itinerary는 일별 일정 리스트입니다.
    # days가 4라면 4박 5일이므로 총 5일치 일정이 만들어집니다.
    itinerary = (
        # 1일차 일정
        [
            f"1일차: {dest} 도착 ✈️ — "
            f"인천 출발, 공항→호텔 이동, 시내 야경 관광"
        ]

        +

        # 2일차부터 days일차까지의 중간 일정

        [
            f"{i + 1}일차: {dest} 탐방 🌏 — "
            f"{'박물관·문화 탐방' if i % 2 == 0 else '쇼핑·맛집 투어'}"
            for i in range(1, days)
        ]

        +

        # 마지막 날 일정

        [
            f"{days + 1}일차: 자유 시간 후 공항 이동, 귀국 ✈️"
        ]

    )

    return {
        # 완성된 일정 리스트를 State에 저장합니다.
        "itinerary": itinerary,
        # 로그는 두 개를 추가합니다.
        # messages는 operator.add 덕분에 기존 로그 뒤에 이어붙습니다.
        "messages": [
            f"🌏 해외 일정 {len(itinerary)}일 수립 완료",
            "※ 출국 전 비자 확인 및 현지 화폐 환전 필수",
        ],
    }

def plan_domestic(state: TravelState) -> dict:
    """
    Node 3-B: 국내 일정 수립 Node
    국내 여행일 때 실행됩니다.
    """

    dest = state["destination"]
    days = state["days"]

    itin = (
        [
            f"1일차: {dest} 출발 🚄 — "
            f"KTX 이동, 숙소 체크인, 근처 탐방"
        ]

        +

        [
            f"{i + 1}일차: {dest} 관광 — "
            f"{'자연·풍경' if i % 2 == 0 else '맛집·카페·쇼핑'}"
            for i in range(1, days)
        ]

        +

        [
            f"{days + 1}일차: 마지막 관광 후 귀가 🏠"
        ]
    )

    return {
        "itinerary": itin,
        "messages": [
            f"🚄 국내 일정 {len(itin)}일 수립 완료",
            "※ KTX 사전 예매 시 30% 할인",
        ],
    }

def recommend_hotels(state: TravelState) -> dict:

    """

    Node 4: 숙소 추천 Node

    목적지와 예산에 맞춰 가상의 숙소 3곳을 추천합니다.

    """

    dest = state["destination"]

    budget = state["budget"]

    days = state["days"]

    # 총 예산의 30%를 숙박비로 배정하고,

    # 박 수로 나누어 1박 평균 예산을 계산합니다.

    per = int(budget * 0.30 / days)

    hotels = [
        {
            "이름": f"{dest} 프리미엄 호텔",
            "1박가격": per,
            "평점": 4.5,
            "특징": "조식 포함, 수영장",
        },

        {
            "이름": f"{dest} 비즈니스 호텔",
            "1박가격": int(per * 0.7),
            "평점": 4.1,
            "특징": "깔끔·교통 편리",
        },

        {
            "이름": f"{dest} 게스트하우스",
            "1박가격": int(per * 0.4),
            "평점": 3.8,
            "특징": "가성비 최고",
        },
    ]

    return {
        "hotels": hotels,
        "messages": [
            f"🏨 숙소 3곳 추천 (1박 평균 {per}만원)"
        ],
    }
def plan_budget(state: TravelState) -> dict:

    """

    Node 5: 예산 배분 Node

    """

    b = state["budget"]

    plan = {

        "항공/교통": int(b * 0.35),

        "숙박": int(b * 0.30),

        "식비": int(b * 0.20),

        "관광/액티비티": int(b * 0.10),

        "기타/비상금": int(b * 0.05),

    }

    # 소수점 버림으로 생긴 차액을 보정합니다.

    plan["기타/비상금"] += b - sum(plan.values())

    return {

        "budget_plan": plan,

        "messages": [

            f"💰 예산 배분 완료 ({sum(plan.values())}만원)"

        ],

    }

def create_summary(state: TravelState) -> dict:

    """
    Node 6: 최종 보고서 작성 Node
    """
    bp = state["budget_plan"]
    hotels = state["hotels"]
    itin = state["itinerary"]
    summary = "\n".join([

        "=" * 45,
        " ✈️ 여행 계획 완성!",
        "=" * 45,

        f" 목적지 : {state['destination']}",
        f" 기간 : {state['days']}박 {state['days'] + 1}일",
        f" 총 예산 : {state['budget']}만원",
        "",
        " [ 예산 배분 ]",
        *[
            f" {k:<14}: {v:>4}만원"
            for k, v in bp.items()
        ],

        "",
        " [ 추천 숙소 TOP 3 ]",
        *[
            f" {h['이름']} — "
            f"{h['1박가격']}만원/박 "
            f"★{h['평점']} ({h['특징']})"
            for h in hotels
        ],

        "",
        " [ 일정 요약 ]",

        *[
            f" {d}"
            for d in itin
        ],
        "=" * 45,
    ])

    return {
        "summary": summary,
        "messages": ["✅ 여행 계획 완성!"],
    }
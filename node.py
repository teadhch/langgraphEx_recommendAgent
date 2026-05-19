# ─────────────────────────────────────────────────────────────
# step02_node.py
# LangGraph의 Node 함수를 작성하는 예제
# ─────────────────────────────────────────────────────────────
# 이 파일은 앞에서 정의한 TravelState와 make_initial_state가
# 이미 있다고 가정합니다.
#
# 실제 프로젝트에서는 다음처럼 import할 수 있습니다.
# from TravelState import TravelState, make_initial_state
# ─────────────────────────────────────────────────────────────
# Node 작성 규칙
# ─────────────────────────────────────────────────────────────
#
# LangGraph에서 Node는 일반 Python 함수입니다.
# 단, 다음 규칙을 지키는 것이 좋습니다.
#
# 1. 매개변수로 state를 받는다.
#       def node_name(state: TravelState) -> dict:
#
# 2. State 전체를 반환하지 않는다.
#       변경할 필드만 dict로 반환한다.
#
# 3. 반환된 dict는 LangGraph가 기존 State에 자동 병합한다.
#
# 예:
#     return {"destination": "태국 방콕"}
#
# 그러면 기존 State의 destination 값만 바뀌고
# budget, days 등 다른 값은 그대로 유지됩니다.
from travelState import TravelState, make_initial_state

def analyze_input(state):
    """
    Node 1: 사용자 입력값을 검증하는 함수입니다.
    역할:
    -----
    - 예산이 너무 적지 않은지 확인합니다.
    - 여행 일수가 정상 범위인지 확인합니다.
    - 문제가 없으면 messages에 입력 확인 로그를 추가합니다.
    매개변수:
    --------
    state:
        현재 그래프의 전체 State입니다.
    반환값:
    -------
    dict:
        업데이트할 필드만 담은 딕셔너리입니다.
    이 Node는 budget이나 days 값을 변경하지 않습니다.
    단지 검증 후 messages에 로그만 추가합니다.
    """
    # state에서 예산과 여행일수를 꺼낸다
    budget = state['budget']
    days = state['days']

    # 예산 유효성 검사
    # ─────────────────────────────────────────────
    # 예산이 50만원보다 작으면 여행 계획을 세우기 어렵다고 판단합니다.
    # 이 경우 ValueError를 발생시켜 그래프 실행을 중단합니다.
    if budget < 50:
        raise ValueError(
            f"예산이 너무 적습니다 "
            f"(입력: {budget}만원, 최소: 50만원)"
        )
    # ─────────────────────────────────────────────
    # 여행 일수 유효성 검사
    # ─────────────────────────────────────────────
    # days는 1 이상 30 이하만 허용합니다.
    # 0일이나 31일 이상은 예제 범위를 벗어난 값으로 봅니다.
    if days < 1 or days > 30:
        raise ValueError(
            f"여행 일수 오류 "
            f"(입력: {days}일, 가능: 1~30일)"
        )

    # 사용자가 입력한 값을 보기 좋은 메시지로 만듭니다.
    # days=4라면 실제 여행 기간은 4박 5일입니다.

    msg = f"✈️ 입력 확인: {days}박 {days + 1}일, 예산 {budget}만원"
    return {
        'messages' : {msg}
    }

def recommend_destination(state: TravelState) -> dict:
    """
    Node 2: 예산과 여행 일수에 따라 목적지를 추천하는 함수입니다.
    역할:
    -----
    - budget과 days를 읽습니다.
    - 조건에 따라 적절한 여행지를 추천합니다.
    - 추천지가 해외인지 국내인지도 함께 판단합니다.
    - destination, is_overseas, messages를 업데이트합니다.
    반환 필드:
    ----------
    destination:
        추천 목적지입니다.
    is_overseas:
        해외 여행 여부입니다.
        이후 조건부 Edge에서 이 값을 사용합니다.
    messages:
        처리 로그입니다.
    """
        # state에서 예산과 여행일수를 꺼낸다
    budget = state['budget']
    days = state['days']
    # ─────────────────────────────────────────────
    # 목적지 추천 규칙
    # ─────────────────────────────────────────────
    # 이 예제에서는 실제 AI 추천이 아니라
    # 예산과 일수에 따른 간단한 규칙 기반 추천입니다.
    #
    # 예산 300만원 이상 + 5박 이상 → 일본 도쿄
    # 예산 200만원 이상 + 3박 이상 → 태국 방콕
    # 예산 150만원 이상 → 국내 제주도
    # 그 외 → 국내 부산

    if budget >= 300 and days >= 5:
        destination = "일본 도쿄"
        is_overseas = True

    elif budget >= 200 and days >= 3:
        destination = "태국 방콕"
        is_overseas = True

    elif budget >= 150:
        destination = "국내 제주도"
        is_overseas = False

    else:
        destination = "국내 부산"
        is_overseas = False

    # 로그 메시지를 생성합니다.
    msg = (
        f"🧭 목적지 추천: {destination} "
        f"({'해외' if is_overseas else '국내'})"
    )

    # 이 Node는 destination과 is_overseas를 새로 채웁니다.
    # messages에는 추천 완료 로그를 추가합니다.

    return {
        "destination": destination,
        "is_overseas": is_overseas,
        "messages": [msg],
    }

# ─────────────────────────────────────────────────────────────
# Node 단독 실행 테스트
# ─────────────────────────────────────────────────────────────
#
# LangGraph에 넣기 전에도 Node는 일반 함수처럼 테스트할 수 있습니다.
# 이것이 매우 중요합니다.
#
# 그래프 전체가 복잡해지기 전에
# 각 Node가 정상적으로 동작하는지 따로 확인할 수 있기 때문입니다.
test_state = make_initial_state(budget=250, days=4)
# analyze_input Node만 단독 실행
result = analyze_input(test_state)
print("analyze_input 반환:", result)
# 예상 결과:
# {
#   "messages": ["✈️ 입력 확인: 4박 5일, 예산 250만원"]
# }
# recommend_destination Node만 단독 실행
result2 = recommend_destination(test_state)
print("recommend_destination 반환:", result2)
# 예상 결과:
# {
#   "destination": "태국 방콕",
#   "is_overseas": True,
#   "messages": ["🧭 목적지 추천: 태국 방콕 (해외)"]
# }
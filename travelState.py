# ── step04_travel_nodes.py ───────────────────────────────────────────────
"""
여행 계획 그래프의 Node 함수 7개를 구현합니다.
각 Node는 State에서 필요한 값만 읽고, 자신의 필드만 업데이트합니다.
"""
from typing import TypedDict, Annotated
import operator

# TypedDict : 딕셔너리처럼 사용하지만, 어떤 key에 해당하는 데이터 타입을 정의 할 수 있습니다.
# 예) state["budget"]은 int타입이어야 한다. 라는 구조를 명확하게 하기 위해...


class TravelState(TypedDict) :
    """
    여행 계획 그래프 전체에서 공유할 State 정의입니다.
    State란?
    --------
    LangGraph 안에서 모든 Node가 함께 사용하는 데이터 저장소입니다.
    쉽게 말하면,
    여행 계획 작업을 진행하면서 계속 들고 다니는 '작업 파일'입니다.
    예를 들어:
    - 사용자가 입력한 예산
    - 추천된 목적지
    - 만들어진 여행 일정
    - 추천 숙소
    - 예산 배분표
    - 최종 보고서
    이런 정보가 모두 State 안에 저장됩니다.
    왜 TypedDict를 사용할까?
    ----------------------

    일반 dict를 쓰면 key 이름을 실수해도 바로 알아차리기 어렵습니다.
    예:
        state["budegt"]  # 오타
    TypedDict를 사용하면 코드 편집기나 타입 검사 도구가
    어느 정도 실수를 잡아줄 수 있습니다.
    """
    # 사용자 입력 필드
    budget: int # 예산
    days: int # 일정. (예 : 4박 5일 -> 4)

    # 그래프 실행 중 자동으로 채워지는 필드=======================
    destination : str   # 추천 목적지
    is_overseas : bool  # 국내/해외     (해외:True, 국내:False)
    # 여행 일정 목록
    # [
    #    "1일차" : "태국 방콕 도착",
    #     "2일차" : "박물관 탐방",
    # ]
    itinerary: list     

    # 추천 숙소 목록
    # [
        # {"이름" : "방콕 5성급 프리미엄 호텔", "1박 가격" : 18, "평점" : 4.7},
    # ]
    hotels: list

    # 항목별 예산 배분 결과
    # {
    #      "항공/교통" : 87,
    #      "숙박" : 75,
    #      "식비" : 60,
    #      "기타경비" : 30
    # }
    budget_plan: dict

    # 최종 여행 계획 보고서 
    summary: str

    # 특수 필드 : messages
    # messages : 각 Node가 실행될 때마다 처리 로그를 남기는 리스트
    messages: Annotated[list, operator.add]

    # 중요한 부분:
    # Annotated[list, operator.add]
    #
    # 일반 list는 새 값이 들어오면 기존 값이 덮어써질 수 있습니다.
    # 하지만 Annotated[list, operator.add]를 사용하면
    # 새 리스트가 기존 리스트 뒤에 이어붙습니다.
    #
    # 예:
    # 기존 messages = ["입력 확인 완료"]
    # 어떤 Node가 {"messages": ["목적지 추천 완료"]} 반환
    #
    # 결과:
    # ["입력 확인 완료", "목적지 추천 완료"]
    #
    # 따라서 전체 처리 과정을 순서대로 기록할 수 있습니다.

def make_initial_state(budget:int, days:int) -> TravelState:
    """
    그래프 실행을 시작하기 위한 초기 State를 만드는 함수입니다.
    매개변수:
    --------
    budget:
        사용자가 입력한 예산입니다.
        단위는 만원입니다.
    days:
        사용자가 입력한 여행 박 수입니다.
    반환값:
    -------
    TravelState:
        LangGraph에 전달할 초기 State 딕셔너리입니다.
    왜 빈 값들을 미리 넣어둘까?
    -------------------------
    그래프가 실행되기 전에는 destination, itinerary, hotels 등이 없습니다.
    하지만 State 구조상 필요한 key들이므로
    일단 빈 문자열, 빈 리스트, 빈 딕셔너리로 초기화합니다.
    이후 각 Node가 자기 역할에 맞게 값을 채웁니다.
    """
    return{
        # 사용자가 처음 제공한 값
        "budget": budget,
        "days": days,
        # 목적지 추천 Node가 나중에 채울 값
        "destination": "",
        # 목적지가 해외인지 국내인지 저장할 값
        # 아직 목적지가 정해지지 않았으므로 기본값 False
        "is_overseas": False,
        # 일정 수립 Node가 채울 값
        "itinerary": [],
        # 숙소 추천 Node가 채울 값
        "hotels": [],
        # 예산 배분 Node가 채울 값
        "budget_plan": {},
        # 최종 보고서 작성 Node가 채울 값
        "summary": "",
        # 전체 실행 로그를 저장할 리스트
        "messages": [],
    }

# ─────────────────────────────────────────────────────────────
# State 생성 테스트
# ─────────────────────────────────────────────────────────────
# 예산 250만원, 4박 여행이라는 초기 State를 만듭니다.
state = make_initial_state(budget=250, days=4)
# 전체 State 출력
print("초기 State:", state)
print()
# budget 값만 확인
print("budget:", state["budget"])  # 250
# days 값만 확인
print("days:", state["days"])      # 4
# 아직 어떤 Node도 실행되지 않았으므로 messages는 빈 리스트입니다.
print("messages:", state["messages"])  # []
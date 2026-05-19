# ── step05_travel_graph.py ───────────────────────────────────────────────
"""
step04에서 만든 Node 7개를 StateGraph로 조립하고 실행합니다.

실행 방법:
    python step05_travel_graph.py
"""
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

# step04의 State 정의 + Node 함수들 임포트
# (같은 파일에 있다면 임포트 불필요)
from travel_nodes import (
    TravelState,
    analyze_input, recommend_destination,
    plan_overseas, plan_domestic,
    recommend_hotels, plan_budget, create_summary,
)


# ── 라우터 함수 ───────────────────────────────────────────────────────────
def route_by_destination(state: TravelState) -> str:
    """
    조건부 엣지 라우터.
    is_overseas 값에 따라 다음 Node를 결정합니다.
    반환값이 add_conditional_edges 딕셔너리의 키와 매핑됩니다.
    """
    return "plan_overseas" if state["is_overseas"] else "plan_domestic"


# ── 그래프 조립 ───────────────────────────────────────────────────────────
def build_travel_graph() -> StateGraph:
    """
    여행 계획 그래프를 조립하고 컴파일된 그래프를 반환합니다.
    """
    builder = StateGraph(TravelState)

    # ① Node 등록 (이름, 함수)
    builder.add_node("analyze_input",         analyze_input)
    builder.add_node("recommend_destination", recommend_destination)
    builder.add_node("plan_overseas",         plan_overseas)
    builder.add_node("plan_domestic",         plan_domestic)
    builder.add_node("recommend_hotels",      recommend_hotels)
    builder.add_node("plan_budget",           plan_budget)
    builder.add_node("create_summary",        create_summary)

    # ② 시작 Node 지정
    builder.set_entry_point("analyze_input")

    # ③ 일반 엣지 (A → B: 항상 이 순서)
    builder.add_edge("analyze_input", "recommend_destination")

    # ④ 조건부 엣지 (recommend_destination → 해외 or 국내 분기)
    builder.add_conditional_edges(
        "recommend_destination",    # 분기 시작 Node
        route_by_destination,       # 라우터 함수
        {
            "plan_overseas": "plan_overseas",   # 해외면 이쪽
            "plan_domestic": "plan_domestic",   # 국내면 이쪽
        }
    )

    # ⑤ 분기 후 합류 → 이후 일반 엣지
    builder.add_edge("plan_overseas",    "recommend_hotels")
    builder.add_edge("plan_domestic",    "recommend_hotels")
    builder.add_edge("recommend_hotels", "plan_budget")
    builder.add_edge("plan_budget",      "create_summary")
    builder.add_edge("create_summary",   END)

    # compile(): 그래프를 실행 가능한 형태로 변환
    return builder.compile()

# ── 실행 ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    graph = build_travel_graph()

    # 입력: 사용자가 제공하는 예산과 일수
    user_input = {
        "budget"     : 250,   # 250만원
        "days"       : 4,     # 4박 5일
        # 나머지 필드는 비워두기 (각 Node가 채워줌)
        "destination": "",
        "is_overseas": False,
        "itinerary"  : [],
        "hotels"     : [],
        "budget_plan": {},
        "summary"    : "",
        "messages"   : [],
    }

    print("여행 계획 생성 중...\n")

    # invoke(): 그래프 전체 실행
    result = graph.invoke(user_input)

    # 처리 로그 출력
    print("[ 처리 순서 ]")
    for msg in result["messages"]:
        print(f"  {msg}")

    # 최종 보고서 출력
    print()
    print(result["summary"])

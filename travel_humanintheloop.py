from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# 함수 임포트
from travel_nodes import (
    TravelState,
    analyze_input, recommend_destination,
    plan_overseas, plan_domestic,
    recommend_hotels, plan_budget, create_summary,
)
from travel_graph import route_by_destination

def build_hil_graph():
    """
    Human-in-the-loop가 포함된 여행 계획 그래프.

    interrupt_before=["recommend_hotels"]:
        recommend_hotels Node 실행 직전에 그래프가 중단됩니다.
        사용자가 목적지를 확인한 뒤 재개 명령을 내리면 계속 실행됩니다.

    checkpointer=MemorySaver():
        중단 시점의 State를 메모리에 저장합니다.
        재개 시 저장된 State에서 이어서 실행합니다.
    """
    builder = StateGraph(TravelState)   # 그래프에서 사용되는 모든 노드가 공유하는 데이터 저장소
    builder.add_node("analyze_input",         analyze_input)
    builder.add_node("recommend_destination", recommend_destination)
    builder.add_node("plan_overseas",         plan_overseas)
    builder.add_node("plan_domestic",         plan_domestic)
    builder.add_node("recommend_hotels",      recommend_hotels)
    builder.add_node("plan_budget",           plan_budget)
    builder.add_node("create_summary",        create_summary)

    builder.set_entry_point("analyze_input")
    builder.add_edge("analyze_input", "recommend_destination")      # edge 노드끼리 연결
    builder.add_conditional_edges(      # 조건부 에지
        "recommend_destination", route_by_destination,  #첫번째 값에따라
        {"plan_overseas": "plan_overseas", "plan_domestic": "plan_domestic"}    #왼쪽으로 갈지 오른쪽으로갈지
    )
    builder.add_edge("plan_overseas",    "recommend_hotels")
    builder.add_edge("plan_domestic",    "recommend_hotels")
    builder.add_edge("recommend_hotels", "plan_budget")
    builder.add_edge("plan_budget",      "create_summary")
    builder.add_edge("create_summary",   END)

    checkpointer = MemorySaver()    # State 저장소 (중단 지점을 기록 하는 객체)
    
    return builder.compile(
        checkpointer=checkpointer, 
        interrupt_before=["recommend_hotels"]   # "recommend_hotels" 노드 실행 전에 중단
        )

if __name__ == "__main__":

    graph = build_hil_graph()

    # thread_id: 이 대화 세션의 고유 ID
    # 재개 시 같은 thread_id를 사용해야 중단된 State를 찾습니다
    config = {"configurable": {"thread_id": "travel-session-001"}}

    init_state = {
        "budget": 250, "days": 4,
        "destination": "", "is_overseas": False,
        "itinerary": [], "hotels": [], "budget_plan": {},
        "summary": "", "messages": [],
    }

    # ── 1차 실행 ─────────────────────────────────────────────────────────
    print("[ 1차 실행 — 목적지 추천까지 ]")
    result1 = graph.invoke(init_state, config=config)

    print(f"추천 목적지: {result1['destination']}")
    print(f"처리 로그 : {result1['messages']}")
    print(f"숙소 목록  : {result1['hotels']}  ← 아직 비어있음 (중단됨)")

    # ── 사용자 확인 ───────────────────────────────────────────────────────
    print()
    answer = input(f"'{result1['destination']}'(으)로 여행 계획을 계속 진행할까요? [Y/n]: ")

    if answer.strip().lower() == "n":
        print("여행 계획을 취소합니다.")
        exit()

    # ── 2차 실행 (재개) ───────────────────────────────────────────────────
    # None을 입력으로 넘기면 중단된 지점에서 이어서 실행
    # 동일한 config(thread_id)를 사용해야 중단 지점을 찾을 수 있음
    print()
    print("[ 2차 실행 — 숙소·예산·보고서 완성 ]")
    result2 = graph.invoke(None, config=config)

    print()
    print(result2["summary"])
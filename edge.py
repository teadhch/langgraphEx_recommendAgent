# ─────────────────────────────────────────────────────────────
# step03_edge.py
# LangGraph에서 Node를 Edge로 연결하는 예제
# ─────────────────────────────────────────────────────────────

# StateGraph:
# LangGraph에서 그래프를 조립할 때 사용하는 핵심 클래스입니다.
#
# END:
# 그래프 종료 지점을 나타내는 특별한 상수입니다.

from langgraph.graph import StateGraph, END
from travelState import TravelState, make_initial_state
from node import analyze_input, recommend_destination

def route_by_destination(state: TravelState) -> str :
    """
    조건부 Edge에서 사용할 라우터 함수입니다.
    역할:
    -----
    현재 State를 보고 다음에 실행할 Node 이름을 결정합니다.
    이 예제에서는 is_overseas 값을 확인합니다.
    - 해외 여행이면 "plan_overseas" 반환
    - 국내 여행이면 "plan_domestic" 반환
    반환값:
    -------
    str:
        다음에 실행할 경로 이름입니다.
    주의:
    -----
    이 함수가 반환하는 문자열은
    add_conditional_edges()에 등록한 딕셔너리의 key와 일치해야 합니다.
    """
    if state["is_overseas"] :
        return "plan_overseas"
    else : 
        return "plan_domestic"
    
# 그래프 조립   (StateGraph : 그래프 자체 객체)
builder = StateGraph(TravelState)

# 1) 노드 등록
# add_node('노드이름', 함수)
builder.add_node('analyze_input', analyze_input)
builder.add_node('recommend_destination', recommend_destination)

# builder.add_node("plan_overseas", plan_overseas)
# builder.add_node("plan_domestic", plan_domestic)
# builder.add_node("recommend_hotels", recommend_hotels)
# builder.add_node("plan_budget", plan_budget)
# builder.add_node("create_summary", create_summary)

# 2) 시작 Node 지정 (그래프가 실행될때 엔트리 포인트(진입점))
builder.set_finish_point('analyze_input')

# 3) 일반 Edge 연결
# add_edge('노드이름A', '노드이름B') : A노드가 끝나면 항상 B노드를 실행한다.
builder.add_edge('analyze_input', 'recommend_destination')

# 4) 조건부 Edge 연결
# 국내여행인지 해외여행인지에 따라 서로 다른 노드로 이동해야 한다.
# add_conditional_edges 사용
builder.add_conditional_edges(
    'recommend_destination', # 조건부 분기가 시작되는 Node
    route_by_destination,   # 조건에 따라 어떤 경로로 갈지를 결정하는 함수(라우터 함수)
    # 라우터 함수의 반환값을 실제 호출되어야 하는 Node 이름으로 매핑
    {
        "plan_overseas" : "plan_overseas",
        "plan_domestic" : "plan_domestic"
    }
)

# 5) 분기 후 다시 합류
builder.add_edge('plan_overseas', 'recommend_hotels')
builder.add_edge('plan_domestic', 'recommend_hotels')

# 6) 이후 일정...... (목적지에서의 추천 관광지, 명소 등을 검색하여 일정 등록)
# 7) 숙소추천 -> 예산 배분 -> 최종 보고서 작성 -> 종료
builder.add_edge("recommend_hotels", "plan_budget")
builder.add_edge("plan_budget", "create_summary")

# 종료를 명시 해야 그래프가 정상 종료 된다.
builder.add_edge("create_summary", END)
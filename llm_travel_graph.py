# ── step02_travel_graph_llm.py ────────────────────────────────────────────

"""

이 파일의 목적:

    step01_llm_nodes.py에서 만든 Node들을

    LangGraph의 StateGraph로 연결하고 실행합니다.

중요한 점:

    그래프 구조는 기존 하드코딩 버전과 거의 같습니다.

달라진 점:

    Node 내부에서 LLM을 호출한다는 점입니다.

즉,

    그래프 조립 방식은 그대로이고,

    Node 함수의 내부 구현만 LLM 버전으로 바뀐 구조입니다.

실행 방법:

    python step02_travel_graph_llm.py

"""

# TypedDict, Annotated:

# 이 파일에서는 직접 TravelState를 다시 정의하지는 않지만,

# State 타입을 다룰 때 자주 사용하는 타입 도구입니다.

from typing import TypedDict, Annotated

# operator:

# messages 누적 같은 State 병합 규칙에 사용됩니다.

import operator

# StateGraph:

# LangGraph에서 그래프를 만드는 핵심 클래스입니다.

#

# END:

# 그래프의 종료 지점을 의미합니다.

from langgraph.graph import StateGraph, END

# step01_llm_nodes.py에서 만든 State와 Node 함수들을 가져옵니다.

#

# 이 파일은 "그래프 조립 담당"

# step01_llm_nodes.py는 "Node 구현 담당"

#

# 이렇게 파일을 나누면 코드 역할이 명확해집니다.

from llm_nodes import (

    TravelState,

    analyze_input,

    recommend_destination,

    plan_overseas,

    plan_domestic,

    recommend_hotels,

    plan_budget,

    create_summary,

)

def route_by_destination(state: TravelState) -> str:

    """

    조건부 엣지에서 사용하는 라우터 함수입니다.

    역할:

        추천 목적지가 해외인지 국내인지에 따라

        다음에 실행할 Node 이름을 결정합니다.

    입력:

        state["is_overseas"]

    반환:

        "plan_overseas" 또는 "plan_domestic"

    동작:

        is_overseas가 True이면:

            해외 일정 Node로 이동

        is_overseas가 False이면:

            국내 일정 Node로 이동

    주의:

        반환하는 문자열은 builder.add_conditional_edges()에서

        등록한 key 이름과 일치해야 합니다.

    """

    # is_overseas 값이 True면 해외 일정 Node로 이동합니다.

    # False면 국내 일정 Node로 이동합니다.

    return "plan_overseas" if state["is_overseas"] else "plan_domestic"

def build_travel_graph_llm():

    """

    실제 LLM Node들로 구성된 여행 계획 그래프를 만듭니다.

    전체 흐름:

        analyze_input

              ↓

        recommend_destination

              ↓

        조건 분기

        ┌───────────────────┐

        ↓                   ↓

    plan_overseas      plan_domestic

        ↓                   ↓

        └──────→ recommend_hotels

                       ↓

                  plan_budget

                       ↓

                  create_summary

                       ↓

                      END

    이 함수는 그래프를 '정의'하고 compile()하여 반환합니다.

    실제 실행은 graph.invoke()에서 이루어집니다.

    """

    # StateGraph 생성

    #

    # TravelState를 넘겨주면

    # 이 그래프가 어떤 State 구조를 사용하는지 알 수 있습니다.

    builder = StateGraph(TravelState)

    # ─────────────────────────────────────────────────────────

    # Node 등록

    # ─────────────────────────────────────────────────────────

    #

    # add_node("노드이름", 함수)

    #

    # 노드 이름:

    #   그래프 안에서 사용할 이름입니다.

    #

    # 함수:

    #   실제 실행될 Python 함수입니다.

    #

    # 여기서는 step01_llm_nodes.py에서 만든 함수를 등록합니다.

    # 입력값 검증 Node

    builder.add_node("analyze_input", analyze_input)

    # LLM 목적지 추천 Node

    builder.add_node("recommend_destination", recommend_destination)

    # LLM 해외 일정 작성 Node

    builder.add_node("plan_overseas", plan_overseas)

    # LLM 국내 일정 작성 Node

    builder.add_node("plan_domestic", plan_domestic)

    # LLM 숙소 추천 Node

    builder.add_node("recommend_hotels", recommend_hotels)

    # 코드 기반 예산 배분 Node

    builder.add_node("plan_budget", plan_budget)

    # LLM 최종 보고서 작성 Node

    builder.add_node("create_summary", create_summary)

    # ─────────────────────────────────────────────────────────

    # Edge 연결

    # ─────────────────────────────────────────────────────────

    #

    # Edge는 Node와 Node 사이의 실행 순서를 의미합니다.

    # 그래프 시작 지점을 analyze_input으로 설정합니다.

    # graph.invoke()가 호출되면 가장 먼저 이 Node가 실행됩니다.

    builder.set_entry_point("analyze_input")

    # analyze_input 실행 후 recommend_destination으로 이동합니다.

    builder.add_edge("analyze_input", "recommend_destination")

    # recommend_destination 이후에는 조건부 분기가 발생합니다.

    #

    # route_by_destination 함수가 반환하는 문자열에 따라

    # 다음 Node가 결정됩니다.

    builder.add_conditional_edges(

        "recommend_destination",   # 이 Node가 끝난 뒤 조건 분기 실행

        route_by_destination,      # 다음 Node 이름을 결정하는 함수

        {

            # route_by_destination이 "plan_overseas"를 반환하면

            # 실제 plan_overseas Node로 이동합니다.

            "plan_overseas": "plan_overseas",

            # route_by_destination이 "plan_domestic"을 반환하면

            # 실제 plan_domestic Node로 이동합니다.

            "plan_domestic": "plan_domestic",

        },

    )

    # 해외 일정 작성 후 숙소 추천으로 이동합니다.

    builder.add_edge("plan_overseas", "recommend_hotels")

    # 국내 일정 작성 후에도 숙소 추천으로 이동합니다.

    builder.add_edge("plan_domestic", "recommend_hotels")

    # 숙소 추천 후 예산 배분으로 이동합니다.

    builder.add_edge("recommend_hotels", "plan_budget")

    # 예산 배분 후 최종 보고서 작성으로 이동합니다.

    builder.add_edge("plan_budget", "create_summary")

    # 최종 보고서 작성 후 그래프를 종료합니다.

    builder.add_edge("create_summary", END)

    # compile():

    # 지금까지 등록한 Node와 Edge를 실제 실행 가능한 그래프로 변환합니다.

    return builder.compile()

# ─────────────────────────────────────────────────────────────

# 이 파일을 직접 실행했을 때만 아래 코드가 실행됩니다.

# ─────────────────────────────────────────────────────────────

#

# 다른 파일에서 import할 때는 실행되지 않습니다.

#

# 예:

#   python step02_travel_graph_llm.py

#

# 위처럼 직접 실행하면 아래 코드가 실행됩니다.

if __name__ == "__main__":

    # 그래프를 생성합니다.

    graph = build_travel_graph_llm()

    # 그래프에 넣을 초기 State입니다.

    #

    # LangGraph의 State는 실행 중 계속 업데이트됩니다.

    #

    # 처음부터 모든 필드를 넣어주는 이유:

    #   TravelState에서 필요한 키들이 무엇인지 명확히 보여주기 위해서입니다.

    #

    # 실제로는 일부 필드를 선택적으로 다룰 수도 있지만,

    # 초보자 교안에서는 이렇게 초기값을 명확히 주는 편이 이해하기 좋습니다.

    user_input = {

        # 사용자가 입력한 여행 예산

        "budget": 250,

        # 숙박 일수

        # 4이면 4박 5일 여행으로 처리합니다.

        "days": 4,

        # 아래 필드들은 실행 과정에서 채워질 값입니다.

        "destination": "",

        "is_overseas": False,

        "dest_reason": "",

        "itinerary": [],

        "travel_tips": [],

        "hotels": [],

        "budget_plan": {},

        "summary": "",

        # 각 Node의 처리 로그가 누적될 리스트입니다.

        "messages": [],

    }

    # LLM 호출이 포함되어 있으므로 실행 시간이 약간 걸릴 수 있습니다.

    print("여행 계획 생성 중... (LLM 호출 중)\n")

    # 그래프 실행

    #

    # graph.invoke(user_input)

    #

    # 의미:

    #   초기 State를 그래프에 넣고

    #   entry point부터 END까지 순서대로 실행합니다.

    #

    # 반환값:

    #   모든 Node 실행이 끝난 최종 State입니다.

    result = graph.invoke(user_input)

    # 처리 순서 출력

    #

    # messages는 각 Node가 반환한 로그가 누적된 결과입니다.

    print("[ 처리 순서 ]")

    for msg in result["messages"]:

        print(f"  {msg}")

    # 줄바꿈

    print()

    # 최종 여행 계획 보고서 출력

    print(result["summary"])
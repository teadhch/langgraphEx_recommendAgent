# ── step01_llm_nodes.py ───────────────────────────────────────────────────

"""
이 파일의 목적:
    기존에 하드코딩으로 작성했던 여행 계획 Node를
    실제 LLM을 호출하는 Node로 교체합니다.

교체되는 Node:
    recommend_destination  : 목적지 추천
    plan_overseas          : 해외 여행 일정 작성
    plan_domestic          : 국내 여행 일정 작성
    recommend_hotels       : 숙소 추천
    create_summary         : 최종 보고서 작성

그대로 유지하는 Node:
    analyze_input          : 입력값 검증
    plan_budget            : 예산 배분 계산

왜 일부는 LLM으로 바꾸고, 일부는 코드로 유지할까요?
    LLM이 잘하는 일:
        - 자연어 판단
        - 이유 설명
        - 추천 문장 작성
        - 보고서 작성
        - 관광지나 숙소 후보 제안

    코드가 더 잘하는 일:
        - 숫자 검증
        - 범위 검사
        - 예산 합계 계산
        - 정해진 규칙을 정확하게 적용하는 일

즉, 이 예제는
    "LLM에게 모든 것을 맡기는 코드"가 아니라
    "LLM과 일반 코드를 역할에 맞게 나누는 구조"를 보여줍니다.
"""

# os:
# 환경변수 등을 다룰 때 사용하는 기본 모듈입니다.
# 이 예제에서는 직접 많이 쓰지는 않지만, 환경 설정 관련 코드에서 자주 사용됩니다.

import os
# TypedDict:
# State의 구조를 딕셔너리 형태로 정의할 때 사용합니다.
#
# Annotated:
# 특정 필드에 추가 규칙을 붙일 때 사용합니다.
# 여기서는 messages 필드에 operator.add를 붙여
# 여러 Node의 메시지가 누적되도록 합니다.
#
# List:
# 리스트 안에 어떤 타입이 들어가는지 표시할 때 사용합니다.
from typing import TypedDict, Annotated, List
# operator.add:
# LangGraph에서 State의 특정 필드를 병합할 때 사용합니다.
# messages: Annotated[list, operator.add]
# 라고 작성하면 각 Node가 반환한 messages 리스트가 덮어쓰기 되지 않고 누적됩니다.
import operator
# load_dotenv:
# .env 파일에 저장된 OPENAI_API_KEY 등을 환경변수로 불러옵니다.
from dotenv import load_dotenv
# BaseModel, Field:
# LLM의 출력 형식을 Pydantic 모델로 정의할 때 사용합니다.
from pydantic import BaseModel, Field
# ChatOpenAI:
# OpenAI Chat 모델을 LangChain에서 사용할 수 있게 해주는 클래스입니다.
from langchain_openai import ChatOpenAI
# ChatPromptTemplate:
# system 메시지와 human 메시지를 구조적으로 만들기 위한 도구입니다.
# 문자열을 그냥 합치는 것보다 역할 구분이 명확해집니다.
from langchain_core.prompts import ChatPromptTemplate
# ─────────────────────────────────────────────────────────────
# .env 파일 로드
# ─────────────────────────────────────────────────────────────
# 현재 프로젝트 폴더에 있는 .env 파일을 읽습니다.
#
# 예:
# OPENAI_API_KEY=sk-proj-...
#
# 이 코드가 실행되어야 ChatOpenAI가 API 키를 사용할 수 있습니다.
load_dotenv()
# ── LLM 초기화 ────────────────────────────────────────────────────────────
# 이 예제 전체에서 사용할 LLM 객체입니다.
#
# model:
# 사용할 모델 이름입니다.
#
# temperature:
# 답변의 다양성, 창의성을 조절합니다.
#
# 0.0:
#   매우 안정적이고 예측 가능한 답변
#
# 0.7:
#   여행 추천처럼 어느 정도 창의성과 자연스러움이 필요한 작업에 적합
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
)

# ══════════════════════════════════════════════════════════════════════════
# Pydantic 출력 스키마 정의
# ══════════════════════════════════════════════════════════════════════════
#
# 여기서 정의하는 클래스들은 LLM 응답의 "그릇"입니다.
#
# LLM이 자유롭게 긴 문장을 반환하면 프로그램이 처리하기 어렵습니다.
# 그래서 목적지 추천 결과, 일정 결과, 숙소 추천 결과를
# 각각 정해진 구조로 받습니다.
#
# 핵심 패턴:
#
#     llm.with_structured_output(스키마클래스)
#
# 이 패턴을 사용하면 LLM 응답을 Pydantic 객체로 받을 수 있습니다.

class DestinationOutput(BaseModel):
    """
    Node 2: recommend_destination의 출력 스키마
    이 스키마는 LLM이 추천 목적지를 반환할 때 사용합니다.
    LLM은 반드시 아래 3개 값을 채워야 합니다.
        1. destination : 추천 목적지
        2. is_overseas : 해외 여행 여부
        3. reason      : 추천 이유
    """
    # 추천 목적지 이름입니다.
    # 예: "태국 방콕", "일본 오사카", "국내 제주도"
    destination: str = Field(
        description="추천 목적지 이름 (예: 태국 방콕, 국내 제주도)"
    )
    # 해외 여행인지 국내 여행인지 구분하는 값입니다.
    # 이 값은 뒤에서 조건부 라우팅에 사용됩니다.
    #
    # True  → plan_overseas Node로 이동
    # False → plan_domestic Node로 이동
    is_overseas: bool = Field(
        description="해외 여행이면 True, 국내 여행이면 False"
    )
    # LLM이 왜 이 목적지를 추천했는지 설명하는 문장입니다.
    # 나중에 최종 보고서에도 사용됩니다.
    reason: str = Field(
        description="이 목적지를 추천하는 이유를 2~3문장으로 설명"
    )

class ItineraryOutput(BaseModel):
    """
    Node 3: plan_overseas / plan_domestic의 출력 스키마
    해외 일정이든 국내 일정이든
    결과 구조는 동일하게 받습니다.
    반환값:
        itinerary : 일별 일정 리스트
        tips      : 여행 팁 리스트
    """
    # 일별 여행 일정입니다.
    #
    # 예:
    # [
    #   "1일차: 인천 출발 → 방콕 도착 → 카오산로드 야시장",
    #   "2일차: 왕궁, 왓포 사원, 짜오프라야강 유람선",
    #   ...
    # ]

    itinerary: List[str] = Field(
        description="일별 일정 리스트. 각 항목은 '1일차: 내용' 형식으로 작성"
    )
    # 여행 팁입니다.
    #
    # 해외 여행이면:
    #   비자, 환전, 유심, 교통카드 등
    #
    # 국내 여행이면:
    #   KTX, 렌터카, 대중교통, 예약 팁 등
    tips: List[str] = Field(
        description="여행 팁 2~3가지 (비자, 환전, 교통, 음식 등 실용적인 내용)"
    )

class HotelItem(BaseModel):
    """
    숙소 1개를 표현하는 스키마
    HotelsOutput 안에서 이 HotelItem이 리스트 형태로 사용됩니다.
    즉,
        HotelItem = 숙소 하나
        HotelsOutput = 숙소 여러 개
    라고 이해하면 됩니다.
    """

    # 숙소 이름입니다.
    # 실제 존재하는 숙소 이름을 받도록 설명을 작성했습니다.
    name: str = Field(
        description="숙소 이름 (실제 존재하는 숙소명)"
    )

    # 1박 가격입니다.
    # 단위는 '만원'입니다.
    #
    # 예:
    # 20 → 20만원/박

    price_per_night: int = Field(
        description="1박 가격 (만원 단위 정수)"
    )

    # 숙소 평점입니다.
    # 5점 만점 기준으로 받습니다.
    rating: float = Field(
        description="평점 (5점 만점, 소수점 1자리)"
    )

    # 숙소의 특징입니다.
    #
    # 예:
    # "시내 중심, 쇼핑몰 연결"
    # "교통 편리, 깔끔한 시설"

    features: str = Field(
        description="숙소 특징 한 줄 설명"
    )

class HotelsOutput(BaseModel):
    """
    Node 4: recommend_hotels의 출력 스키마
    숙소 추천 결과 전체를 담는 모델입니다.
    hotels 필드 안에 HotelItem 객체들이 리스트로 들어갑니다.
    """

    # 숙소 3곳 추천 결과입니다.
    # 각 항목은 HotelItem 구조를 따릅니다.

    hotels: List[HotelItem] = Field(
        description="가격대별 숙소 3곳 추천"
    )

class TravelState(TypedDict):

    # ── 입력 필드 ─────────────────────────────────────────────
    # 사용자가 입력한 총 예산입니다.
    # 단위는 '만원'입니다.
    budget: int
    # 여행 숙박 일수입니다.
    # 예: days=4이면 4박 5일로 처리합니다.
    days: int
    # ── 기존 필드 ─────────────────────────────────────────────
    # 추천 목적지 이름입니다.
    destination: str
    # 해외 여행 여부입니다.
    # recommend_destination Node가 이 값을 채웁니다.
    is_overseas: bool
    # 일별 여행 일정 리스트입니다.
    itinerary: list
    # 추천 숙소 리스트입니다.
    hotels: list
    # 예산 배분 결과입니다.
    # 예:
    # {
    #   "항공/교통": 87,
    #   "숙박": 75,
    #   ...
    # }
    budget_plan: dict
    # 최종 여행 계획 보고서입니다.
    summary: str
    # 처리 로그입니다.
    #
    # Annotated[list, operator.add]의 의미:
    # 각 Node가 messages를 반환하면 기존 messages에 이어붙입니다.
    #
    # 예:
    # Node 1 → ["분석 시작"]
    # Node 2 → ["목적지 추천 완료"]
    #
    # 최종 messages:
    # ["분석 시작", "목적지 추천 완료"]
    messages: Annotated[list, operator.add]
    # ── LLM이 채우는 새 필드 ──────────────────────────────────
    # 목적지 추천 이유입니다.
    # recommend_destination Node에서 생성합니다.
    dest_reason: str
    # 여행 팁 리스트입니다.
    # plan_overseas 또는 plan_domestic Node에서 생성합니다.
    travel_tips: list

# ── Node 1: 입력 검증 ─────────────────────────────────────────

def analyze_input(state: TravelState) -> dict:
    """
    입력값 유효성 검사 Node입니다.
    이 Node는 LLM을 사용하지 않습니다.
    이유:
        예산이 50만원 이상인지,
        여행 일수가 1~30일 사이인지 확인하는 일은
        자연어 판단이 아니라 명확한 수치 검사입니다.
    이런 작업은 LLM보다 코드가 더 빠르고 정확합니다.
    입력:
        state["budget"]
        state["days"]
    출력:
        messages에 분석 시작 로그 추가
    예외:
        예산이 너무 작으면 ValueError 발생
        여행 일수가 범위를 벗어나면 ValueError 발생
    """
    # State에서 예산과 여행 일수를 꺼냅니다.
    budget, days = state["budget"], state["days"]
    # 최소 예산 검사입니다.
    # 예산이 50만원보다 작으면 현실적인 여행 계획을 세우기 어렵다고 보고 오류를 발생시킵니다.
    if budget < 50:
        raise ValueError(f"예산 오류: {budget}만원 (최소 50만원)")
    # 여행 일수 검사입니다.
    # days는 숙박 일수입니다.
    # 1박 이상, 30박 이하만 허용합니다.
    if not (1 <= days <= 30):
        raise ValueError(f"일수 오류: {days}일 (1~30일 사이)")
    # 검증에 성공하면 messages에 로그를 추가합니다.
    #
    # 여기서 반환하는 dict는 기존 State에 병합됩니다.
    # messages는 operator.add 규칙 때문에 기존 리스트에 이어붙습니다.
    return {
        "messages": [
            f"✈️  분석 시작: {days}박 {days+1}일, 예산 {budget}만원"
        ]
    }

# ── Node 2: 목적지 추천 ───────────────────────────────────────

def recommend_destination(state: TravelState) -> dict:

    """

    예산과 일수를 기준으로 LLM에게 목적지를 추천받는 Node입니다.

    기존 하드코딩 방식:

        if budget >= 300 and days >= 5:

            destination = "일본 도쿄"

    실제 LLM 방식:

        예산, 기간을 프롬프트로 전달하고

        LLM이 목적지와 추천 이유를 판단하게 합니다.

    이 Node의 핵심:

        llm.with_structured_output(DestinationOutput)

    왜 structured_output을 쓰나요?

        LLM이 자유 문장으로 답하면 목적지, 해외 여부, 추천 이유를

        코드에서 안정적으로 분리하기 어렵습니다.

        그래서 DestinationOutput 형식으로 답하게 만들어

        result.destination

        result.is_overseas

        result.reason

        처럼 바로 접근합니다.

    입력:

        state["budget"]

        state["days"]

    출력:

        destination

        is_overseas

        dest_reason

        messages

    """

    # ChatPromptTemplate은 LLM에게 보낼 메시지 구조를 만듭니다.

    #

    # system:

    #   LLM의 역할을 지정합니다.

    #

    # human:

    #   실제 사용자의 요청 내용을 넣습니다.

    #

    # {budget}, {days}, {total_days}는 나중에 invoke()에서 값이 채워집니다.

    prompt = ChatPromptTemplate.from_messages([

        (

            "system",

            "당신은 여행 전문가입니다. 예산과 일정에 맞는 최적의 여행지를 추천해주세요. "

            "한국 출발 기준으로, 현실적인 예산 범위에서 추천하세요."

        ),

        (

            "human",

            "여행 예산: {budget}만원\n"

            "여행 기간: {days}박 {total_days}일\n\n"

            "위 조건에 맞는 여행지를 추천해주세요."

        ),

    ])

    # prompt | llm.with_structured_output(...)

    #

    # 이 코드는 LCEL 파이프라인입니다.

    #

    # 흐름:

    #   1. prompt가 메시지를 만든다.

    #   2. LLM이 메시지를 읽고 답변한다.

    #   3. 답변을 DestinationOutput 객체로 변환한다.

    chain = prompt | llm.with_structured_output(DestinationOutput)

    # chain.invoke()를 호출하면 실제 LLM 호출이 발생합니다.

    #

    # total_days는 여행 전체 일수입니다.

    # days가 숙박 일수이므로 전체 여행일은 days + 1로 계산합니다.

    result: DestinationOutput = chain.invoke({

        "budget": state["budget"],

        "days": state["days"],

        "total_days": state["days"] + 1,

    })

    # LLM 결과를 State에 병합할 수 있도록 dict로 반환합니다.

    #

    # destination:

    #   추천 목적지

    #

    # is_overseas:

    #   조건부 라우팅에 사용됩니다.

    #

    # dest_reason:

    #   최종 보고서에서 추천 이유로 사용됩니다.

    #

    # messages:

    #   처리 로그에 추가됩니다.

    return {

        "destination": result.destination,

        "is_overseas": result.is_overseas,

        "dest_reason": result.reason,

        "messages": [

            f"🗺️  목적지: {result.destination} "

            f"({'해외' if result.is_overseas else '국내'})"

        ],

    }

# ── Node 3-A: 해외 일정 수립 ──────────────────────────────────

def plan_overseas(state: TravelState) -> dict:
    """
    해외 여행 일정을 LLM이 작성하는 Node입니다.
    이 Node는 recommend_destination에서
    is_overseas가 True일 때 실행됩니다.
    기존 하드코딩 방식:
        "1일차: 목적지 도착"
        "2일차: 문화 탐방"
        처럼 고정된 문자열을 만들었습니다.
    실제 LLM 방식:
        LLM에게 목적지, 여행 기간, 예산을 알려주고
        실제 관광지, 음식, 교통 정보를 포함한 일정을 생성하게 합니다.
    입력:
        destination
        days
        budget
    출력:
        itinerary
        travel_tips
        messages
    """
    # 해외 여행 전문 가이드 역할을 system 메시지로 부여합니다.
    # LLM에게 단순한 요약이 아니라 실제 관광지와 이동 방법까지 포함하라고 지시합니다.
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "당신은 해외 여행 전문 가이드입니다. "
            "실제 관광지, 맛집, 이동 방법을 포함한 구체적인 일정을 작성해주세요. "
            "각 일차는 '1일차: 내용' 형식으로 작성하세요."
        ),
        (
            "human",
            "목적지: {destination}\n"
            "여행 기간: {days}박 {total_days}일\n"
            "예산: {budget}만원\n\n"
            "구체적인 해외 여행 일정과 실용적인 팁을 작성해주세요."
        ),
    ])
    # ItineraryOutput 형식으로 LLM 결과를 받습니다.
    #
    # result.itinerary → 일별 일정 리스트
    # result.tips      → 여행 팁 리스트
    chain = prompt | llm.with_structured_output(ItineraryOutput)
    # LLM 호출
    result: ItineraryOutput = chain.invoke({     # 유형이 틀리면 value error 맞으면 result에 들어감
        "destination": state["destination"],
        "days": state["days"],
        "total_days": state["days"] + 1,
        "budget": state["budget"],
    })
    # 생성된 일정과 팁을 State에 저장합니다.
    return {
        "itinerary": result.itinerary,
        "travel_tips": result.tips,
        "messages": [
            f"🌏  해외 일정 {len(result.itinerary)}일 수립 완료",
            "    ※ 비자 확인 및 현지 화폐 환전 필수",
        ],
    }

def plan_domestic(state: TravelState) -> dict:
    """
    국내 여행 일정을 LLM이 작성하는 Node입니다.
    이 Node는 recommend_destination에서
    is_overseas가 False일 때 실행됩니다.
    해외 일정 Node와 구조는 거의 같습니다.
    차이점은 system 메시지에서
    '국내 여행 전문 가이드' 역할을 준다는 점입니다.
    입력:
        destination
        days
        budget

    출력:
        itinerary
        travel_tips
        messages
    """

    # 국내 여행에 맞는 프롬프트입니다.
    # 국내 여행에서는 KTX, 렌터카, 버스, 지역 맛집 등이 중요할 수 있습니다.

    prompt = ChatPromptTemplate.from_messages([

        (
            "system",
            "당신은 국내 여행 전문 가이드입니다. "
            "실제 관광지, 맛집, 교통편을 포함한 구체적인 일정을 작성해주세요. "
            "각 일차는 '1일차: 내용' 형식으로 작성하세요."
        ),

        (

            "human",

            "목적지: {destination}\n"

            "여행 기간: {days}박 {total_days}일\n"

            "예산: {budget}만원\n\n"

            "구체적인 국내 여행 일정과 교통 팁을 작성해주세요."

        ),

    ])

    # 국내 일정도 해외 일정과 같은 ItineraryOutput 구조로 받습니다.

    chain = prompt | llm.with_structured_output(ItineraryOutput)

    # LLM 호출

    result: ItineraryOutput = chain.invoke({

        "destination": state["destination"],

        "days": state["days"],

        "total_days": state["days"] + 1,

        "budget": state["budget"],

    })

    # State에 일정과 팁을 병합합니다.

    return {

        "itinerary": result.itinerary,

        "travel_tips": result.tips,

        "messages": [

            f"🚄  국내 일정 {len(result.itinerary)}일 수립 완료",

            "    ※ KTX 사전 예매 시 최대 30% 할인",

        ],

    }

# ── Node 4: 숙소 추천 ─────────────────────────────────────────

def recommend_hotels(state: TravelState) -> dict:

    """

    목적지와 예산에 맞는 숙소를 LLM이 추천하는 Node입니다.

    기존 하드코딩 방식:

        f"{destination} 프리미엄 호텔"

        같은 가짜 숙소명을 만들었습니다.

    실제 LLM 방식:

        LLM에게 목적지와 1박 평균 예산을 알려주고

        실제 존재하는 숙소 후보를 추천받습니다.

    이 Node의 중요한 계산:

        per_night = 전체 예산의 30% / 숙박 일수

    이유:

        전체 예산 중 숙박비를 대략 30%로 보고,

        이를 숙박 일수로 나누어 1박 평균 숙소 예산을 계산합니다.

    입력:

        destination

        budget

        days

    출력:

        hotels

        messages

    """

    # 전체 예산 중 30%를 숙박 예산으로 보고,

    # 숙박 일수로 나누어 1박 평균 예산을 구합니다.

    #

    # 예:

    # budget = 250

    # days = 4

    #

    # 250 * 0.30 = 75만원

    # 75 / 4 = 18.75

    # int(...) → 18만원

    per_night = int(state["budget"] * 0.30 / state["days"])

    # 호텔 전문가 역할을 부여합니다.

    # "실제 존재하는 숙소"와 "가격대별 3곳"을 명확히 지시합니다.

    prompt = ChatPromptTemplate.from_messages([

        (

            "system",

            "당신은 호텔 전문가입니다. "

            "실제 존재하는 숙소를 가격대별로 3곳 추천해주세요. "

            "1박 가격은 예산 범위에 맞게 현실적으로 제시하세요."

        ),

        (

            "human",

            "목적지: {destination}\n"

            "1박 평균 예산: {per_night}만원\n"

            "여행 기간: {days}박\n\n"

            "고급·중급·저가 각 1곳씩, 총 3곳을 추천해주세요."

        ),

    ])

    # HotelsOutput 형식으로 LLM 결과를 받습니다.

    #

    # result.hotels는 HotelItem 객체들의 리스트입니다.

    chain = prompt | llm.with_structured_output(HotelsOutput)

    # LLM 호출

    result: HotelsOutput = chain.invoke({

        "destination": state["destination"],

        "per_night": per_night,

        "days": state["days"],

    })

    # Pydantic 객체를 일반 딕셔너리로 변환합니다.

    #

    # 왜 변환할까요?

    # State에는 일반 dict/list 형태로 저장하는 것이 다루기 쉽습니다.

    #

    # h.model_dump()

    #   HotelItem 객체를 다음과 같은 dict로 바꿉니다.

    #

    # {

    #   "name": "...",

    #   "price_per_night": 20,

    #   "rating": 4.6,

    #   "features": "..."

    # }

    hotels_dict = [h.model_dump() for h in result.hotels]

    # 추천 숙소 목록과 처리 메시지를 반환합니다.

    return {

        "hotels": hotels_dict,

        "messages": [

            f"🏨  숙소 {len(hotels_dict)}곳 추천 (1박 평균 {per_night}만원)"

        ],

    }

# ── Node 5: 예산 배분 ─────────────────────────────────────────

def plan_budget(state: TravelState) -> dict:

    """

    전체 예산을 항목별로 배분하는 Node입니다.

    이 Node는 LLM을 사용하지 않습니다.

    이유:

        예산 배분은 정확한 수치 계산이 중요합니다.

        LLM에게 맡기면 합계가 틀리거나 반올림 오차가 발생할 수 있습니다.

    배분 기준:

        항공/교통     35%

        숙박          30%

        식비          20%

        관광/액티비티 10%

        기타/비상금    5%

    입력:

        budget

    출력:

        budget_plan

        messages

    """

    # 전체 예산을 꺼냅니다.

    b = state["budget"]

    # 각 항목별 예산을 계산합니다.

    #

    # int()를 사용하면 소수점 아래가 버려집니다.

    # 예: 87.5 → 87

    plan = {

        "항공/교통": int(b * 0.35),

        "숙박": int(b * 0.30),

        "식비": int(b * 0.20),

        "관광/액티비티": int(b * 0.10),

        "기타/비상금": int(b * 0.05),

    }

    # 반올림 또는 소수점 버림 때문에 합계가 전체 예산과 다를 수 있습니다.

    #

    # 예:

    # 전체 예산이 251만원이면

    # 각 항목을 int로 버리는 과정에서 합계가 251이 안 될 수 있습니다.

    #

    # 그래서 차액을 기타/비상금에 더해

    # 최종 합계가 반드시 전체 예산과 일치하도록 보정합니다.

    plan["기타/비상금"] += b - sum(plan.values())

    # 예산 배분 결과를 State에 저장합니다.

    return {

        "budget_plan": plan,

        "messages": [

            f"💰  예산 배분 완료 (총 {sum(plan.values())}만원)"

        ],

    }

# ── Node 6: 최종 보고서 작성 ─────────────────────────────────

def create_summary(state: TravelState) -> dict:

    """

    지금까지 생성된 모든 정보를 모아

    LLM이 최종 여행 계획 보고서를 작성하는 Node입니다.

    이 Node는 structured_output을 사용하지 않습니다.

    이유:

        최종 보고서는 딕셔너리나 리스트가 아니라

        사람이 읽기 좋은 자연어 문장이 필요하기 때문입니다.

    그래서 여기서는:

        prompt | llm | StrOutputParser()

    구조를 사용합니다.

    입력:

        destination

        days

        budget

        dest_reason

        budget_plan

        hotels

        itinerary

        travel_tips

    출력:

        summary

        messages

    """

    # State에서 필요한 값을 꺼냅니다.

    bp = state["budget_plan"]

    hotels = state["hotels"]

    itin = state["itinerary"]

    # travel_tips는 혹시 없을 수도 있으므로 get()을 사용합니다.

    # 없으면 빈 리스트 []를 기본값으로 사용합니다.

    tips = state.get("travel_tips", [])

    # 최종 보고서 작성용 프롬프트입니다.

    #

    # system:

    #   LLM에게 여행 플래너 역할을 부여합니다.

    #

    # human:

    #   지금까지 그래프가 만든 모든 결과를 전달합니다.

    prompt = ChatPromptTemplate.from_messages([

        (

            "system",

            "당신은 여행 플래너입니다. 아래 여행 계획 정보를 바탕으로 "

            "읽기 좋은 최종 여행 계획 보고서를 작성해주세요."

        ),

        (

            "human",

            "목적지: {destination}\n"

            "기간: {days}박 {total_days}일\n"

            "예산: {budget}만원\n"

            "추천 이유: {reason}\n\n"

            "예산 배분:\n{budget_plan}\n\n"

            "추천 숙소:\n{hotels}\n\n"

            "일정:\n{itinerary}\n\n"

            "여행 팁:\n{tips}\n\n"

            "위 내용을 바탕으로 친근하고 실용적인 여행 계획 보고서를 작성해주세요."

        ),

    ])

    # StrOutputParser:

    # LLM 응답에서 문자열만 꺼내는 출력 파서입니다.

    #

    # create_summary는 자유 형식의 보고서가 필요하므로

    # Pydantic structured_output이 아니라 StrOutputParser를 사용합니다.

    from langchain_core.output_parsers import StrOutputParser

    # LCEL 파이프라인입니다.

    #

    # prompt → llm → 문자열 파서

    chain = prompt | llm | StrOutputParser()

    # 최종 보고서 생성을 위해 LLM을 호출합니다.

    #

    # budget_plan, hotels, itinerary, tips는 원래 dict/list입니다.

    # LLM에게 읽기 좋게 전달하기 위해 문자열로 변환합니다.

    summary = chain.invoke({

        "destination": state["destination"],

        "days": state["days"],

        "total_days": state["days"] + 1,

        "budget": state["budget"],

        "reason": state.get("dest_reason", ""),

        # 예산 배분 dict를 여러 줄 문자열로 변환합니다.

        #

        # 예:

        #   항공/교통: 87만원

        #   숙박: 75만원

        "budget_plan": "\n".join(

            f"  {k}: {v}만원"

            for k, v in bp.items()

        ),

        # 숙소 리스트를 여러 줄 문자열로 변환합니다.

        #

        # 예:

        #   · Centara Grand CentralWorld — 20만원/박 ★4.6 (시내 중심)

        "hotels": "\n".join(

            f"  · {h['name']} — {h['price_per_night']}만원/박 ★{h['rating']} ({h['features']})"

            for h in hotels

        ),

        # 일별 일정 리스트를 여러 줄 문자열로 변환합니다.

        "itinerary": "\n".join(

            f"  {d}"

            for d in itin

        ),

        # 여행 팁 리스트를 여러 줄 문자열로 변환합니다.

        "tips": "\n".join(

            f"  · {t}"

            for t in tips

        ),

    })

    # 최종 보고서와 완료 메시지를 반환합니다.

    return {

        "summary": summary,

        "messages": [

            "✅  여행 계획 완성!"

        ],

    }
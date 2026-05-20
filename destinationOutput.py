# ── with_structured_output 개념 ───────────────────────────────────────────
# ChatOpenAI:
# OpenAI의 Chat 모델을 LangChain 방식으로 사용하기 위한 클래스입니다.
# 쉽게 말해 "LLM 객체"를 만드는 도구입니다.

from langchain_openai import ChatOpenAI
# BaseModel, Field: Pydantic에서 제공하는 데이터 구조 정의 도구입니다.
# LLM에게 "너는 반드시 이런 모양으로 대답해야 해"라고 알려줄 때 사용합니다.
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────
# Pydantic 모델 정의
# ─────────────────────────────────────────────────────────────

# 이 클래스는 LLM의 응답 형식을 미리 정해두는 역할을 합니다.
# 예를 들어 LLM이 자유롭게 이런 식으로 답하면:
# "음... 예산을 보면 태국 방콕이 좋아요. 해외입니다."
#
# 프로그램 입장에서는 destination이 어디인지,
# 해외 여부가 True인지 False인지 안정적으로 뽑기 어렵습니다.
# 그래서 아래처럼 출력 형식을 고정합니다.

class DestinationOutput(BaseModel) :
    # 목적지 이름
    destination: str = Field(
        description="추천 목적지 이름 (예 : 태국 방콕)"
    )

# 해외 여행 여부를 참/거짓(bool)으로 받습니다.
    # 해외면 True, 국내면 False가 들어와야 합니다.
    is_overseas: bool = Field(
        description="해외 여행이면 True, 국내면 False"
    )

    # 목적지를 추천한 이유를 문자열로 받습니다.
    reason: str = Field(
        description="이 목적지를 추천하는 이유 2~3문장"
    )
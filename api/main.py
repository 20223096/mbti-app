from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Literal

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Reason(BaseModel):
    reason: str
    likelihood: Literal["high", "medium", "low"]
    signals_to_check: List[str]
    risk_of_misread: str
class Actions(BaseModel):
    do: List[str]
    avoid: List[str]
class MsgExample(BaseModel):
    tone: str
    text:str

class AnalyzeResponse(BaseModel):
    summary: str
    interpretation: dict
    reasons_top3 : List[Reason]
    actions: Actions
    message_examples: List[MsgExample]
    reality_check : str
    comfort: str
    disclaimer : str

class AnalyzeRequest(BaseModel):
    situation : str
    mbti : str | None = None
    relationship_type : str | None = None
    relationship_state : str | None = None

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    return {
        "summary" : f"상황 요약 : {req.situation[:30]}",
        "interpretation" : {
            "mbti_view" : f"{req.mbti or 'MBTI 미선택'} 관점에서 해석",
            "why_this_matters" : "사용자가 불안해하는 핵심은 '상대의 의도'를 확신하고 싶은 것일 수 있어요."
        },
        "reasons_top3" : [
            {
                "reason" : "상대가 단순히 바빴을 가능성",
                "likelihood" : "medium",
                "signals_to_check" : ["이전에도 비슷했는지", "후속 연락이 오는지"],
                "risk_of_misread" : "바쁨을 무관심으로 단정할 수 있음"
            },
            {
                "reason": "관계 단계/기대치 불일치",
                "likelihood": "high",
                "signals_to_check": ["연락 기대치 합의 여부", "표현 방식 차이"],
                "risk_of_misread": "표현 방식 차이를 감정 부족으로 오해"
            }
        ],
        "actions": {
            "do": ["가벼운 확인 메시지 1회", "반복 패턴을 1~2주 관찰", "내 기대치 정리"],
            "avoid": ["장문의 추궁", "확신 요구로 압박"]
        },
        "message_examples": [
            {"tone": "가볍게", "text": "요즘 바쁜가봐! 시간 되면 얘기하자 🙂"},
            {"tone": "경계선", "text": "내가 요즘 연락이 뜸해서 신경 쓰이더라. 괜찮으면 한번 얘기해볼래?"}
        ],
        "reality_check": "단발성 사건만으로 관계를 단정하긴 어려워요. 반복 패턴인지가 핵심이에요.",
        "comfort": "불안해지는 건 자연스러워요. 확인하고 싶은 마음도 정상이에요.",
        "disclaimer": "MBTI만으로 상대의 의도나 감정을 단정할 수 없어요."
    }
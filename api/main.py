from fastapi import FastAPI
import sqlite3
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import List, Literal, Optional, Dict, Any
import os, json
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import copy
import re
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# MODELS
# ==========================

Role = Literal["user", "assistant"]
DB_PATH = Path(os.environ.get("RULES_DB_PATH", "rules.db"))
ALLOWED_PATCH_PREFIXES = ("user.", "partner.", "context.", "signals.")

# user.xxx / partner.xxx 같은 점(.) 경로만 허용 (최대 8 depth)
PATCH_KEY_RE = re.compile(r"^(user|partner|context|signals)(\.[a-zA-Z0-9_]+){1,8}$")


class ChatMessage(BaseModel):
    role: Role
    content: str

class TraitsProfile(BaseModel):
    type: str
    base: Dict[str, Any]
    state: Dict[str, Any]
    evidence: List[Dict[str, Any]]

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    mbti: Optional[str] = None
    relationship_type: Optional[str] = None
    relationship_state: Optional[str] = None
    traits_profile: Optional[TraitsProfile] = None

class ChatResponse(BaseModel):
    assistant_message: str
    analysis_json: Dict[str, Any]


# ==========================
# OpenAI 설정
# ==========================

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


# ==========================
# 유틸
# ==========================

def deep_merge(base: dict, state: dict):
    merged = copy.deepcopy(base)

    for k, v in state.items():
        if isinstance(v, dict) and k in merged:
            merged[k] = deep_merge(merged.get(k, {}), v)
        else:
            merged[k] = v
    return merged


def merge_traits(req: ChatRequest) -> dict:
    # 1) mbti 결정 우선순위: req.mbti > req.traits_profile.type
    mbti = (req.mbti or (req.traits_profile.type if req.traits_profile else None))

    # 2) DB에서 기본 프로필 로드
    mbti_base = fetch_mbti_profile(mbti)

    # 3) 프론트에서 넘어온 traits_profile(base/state) 합치기
    user_traits = {}
    if req.traits_profile:
        user_traits = deep_merge(req.traits_profile.base or {}, req.traits_profile.state or {})

    # 4) MBTI 기본값 위에 user_traits가 덮어쓰게 병합
    merged = deep_merge(mbti_base, user_traits)
    return merged

PATCH_ITEM_EXAMPLE = '{"path":"context.memory.patterns","value_json":"[\\"연락이 줄어들면 불안해함\\"]"}'
VALUE_JSON_EXAMPLE = 'true -> "true", 3 -> "3", {"a":1} -> "{\\"a\\":1}"'


def build_instructions(req: ChatRequest, merged_traits: dict) -> str:
    type_rules = fetch_relationship_type_rules(req.relationship_type)
    state_rules = fetch_relationship_state_rules(req.relationship_state)

    return f"""
너는 1급 심리 상담사이자 연애/관계 분석 전문가야.
상대방의 MBTI 성향과 현재 관계 상태의 특성을 기반으로, 내담자(사용자)의 불안함을 달래주고 날카로운 통찰을 제공해야 해.

[상대방의 성향(MBTI 등) 데이터]
{json.dumps(merged_traits, ensure_ascii=False)}

[현재 관계 유형 규칙]
{json.dumps(type_rules, ensure_ascii=False)}

[현재 관계 상태 규칙]
{json.dumps(state_rules, ensure_ascii=False)}

======================
assistant_message 작성 규칙 (핵심)
======================
사용자가 직접 읽는 답변이야. 절대 기계적으로 짧게 끝내지마.
다음 흐름으로 3~4 문단의 풍부한 대답을 작성해:
1. 공감 : 사용자의 현재 감정을 부드럽게 읽어주고 안심시킬 것.
2. 성향 기반 분석 : 위 데이터의 'core_drives'나 'communication' 특징을 직접 언급하며 상대방의 행동이 왜 무관심이 아니라 그들만의 방식인지 설명할 것. (예 : "ISTP는 원래 에너지가 낮아서...")
3) 근거 없는 MBTI 단정 금지. certainty가 low면 반드시 대안 후보 제시.
4. 역질문: 대화를 이어가거나 추가 단서를 얻기 위해, 상황에 맞는 구체적인 질문 1개를 마지막에 던질 것.

* 금지사항: JSON 분석 내용을 그대로 복붙하지 말 것. 딱딱한 말투 금지.

""".strip()

def filter_updated_traits_patch(patch) -> list[dict]:
    """
    LLM이 준 updated_traits_patch(list)를 검증/정리해서
    [{path: "...", value: <parsed>}, ...] 형태로 반환
    """
    if not isinstance(patch, list):
        return []

    filtered: list[dict] = []
    for item in patch:
        if not isinstance(item, dict):
            continue

        path = item.get("path")
        value_json = item.get("value_json")

        if not isinstance(path, str) or not isinstance(value_json, str):
            continue

        path = path.strip()

        # prefix 체크 + 패턴 체크
        if not path.startswith(ALLOWED_PATCH_PREFIXES):
            continue
        if not PATCH_KEY_RE.match(path):
            continue

        # value_json은 반드시 JSON 문자열이어야 함
        try:
            value = json.loads(value_json)
        except Exception:
            continue

        # 직렬화 가능 확인
        try:
            json.dumps(value, ensure_ascii=False)
        except Exception:
            continue

        filtered.append({"path": path, "value": value})

    return filtered

def to_responses_input(messages: List[ChatMessage]):
    items = []
    for m in messages[-20:]:  # ← 버그 수정 (슬라이싱)
        content_type = "output_text" if m.role == "assistant" else "input_text"
        items.append({
            "role": m.role,
            "content": [{"type": content_type, "text": m.content}]
        })
    return items

def fetch_relationship_type_rules(type_code: str | None) -> dict:
    if not type_code:
        return {"type_code": None, "display_name": None, "rules": []}

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT display_name, rules_json
        FROM relationship_type_modifiers
        WHERE type_code=? AND is_active=1
        LIMIT 1
    """, (type_code,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"type_code": type_code, "display_name": None, "rules": []}

    display_name, rules_json = row
    payload = json.loads(rules_json)
    return {"type_code": type_code, "display_name": display_name, "rules": payload.get("rules", [])}


def fetch_relationship_state_rules(state_code: str | None) -> dict:
    if not state_code:
        return {"state_code": None, "display_name": None, "rules": []}

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT display_name, rules_json
        FROM relationship_state_modifiers
        WHERE state_code=? AND is_active=1
        LIMIT 1
    """, (state_code,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"state_code": state_code, "display_name": None, "rules": []}

    display_name, rules_json = row
    payload = json.loads(rules_json)
    return {"state_code": state_code, "display_name": display_name, "rules": payload.get("rules", [])}

def fetch_mbti_profile(mbti: str | None) -> dict:
    if not mbti:
        return {}

    mbti = mbti.upper().strip()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT profile_json
        FROM mbti_profiles
        WHERE mbti=? AND is_active=1
        LIMIT 1
    """, (mbti,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return {}

    return json.loads(row[0])

# ==========================
# JSON SCHEMA
# ==========================
CHAT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["assistant_message", "analysis_json"],
    "properties": {
        "assistant_message": {"type": "string"},
        "analysis_json": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "summary",
                "mbti_hypothesis",
                "interpretation",
                "reasons_top3",
                "actions",
                "message_examples",
                "follow_up_questions",
                "updated_traits_patch",
                "confidence",
                "reality_check",
                "comfort",
                "disclaimer"
            ],
            "properties": {
                "summary": {"type": "string"},

                "mbti_hypothesis": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["given", "certainty", "alt_candidates"],
                    "properties": {
                        "given": {"type": "string"},
                        "certainty": {"type": "string", "enum": ["high", "medium", "low"]},
                        "alt_candidates": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 3
                        }
                    }
                },

                "interpretation": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["mbti_view", "why_this_matters"],
                    "properties": {
                        "mbti_view": {"type": "string"},
                        "why_this_matters": {"type": "string"}
                    }
                },

                # ✅ TOP3 이유: 구조 고정
                "reasons_top3": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["reason", "likelihood", "evidence_from_chat", "what_to_check"],
                        "properties": {
                            "reason": {"type": "string"},
                            "likelihood": {"type": "string", "enum": ["high", "medium", "low"]},
                            "evidence_from_chat": {
                                "type": "array",
                                "items": {"type": "string"},
                                "maxItems": 3
                            },
                            "what_to_check": {"type": "string"}
                        }
                    }
                },

                # ✅ 액션: 구조 고정
                "actions": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["do_now", "do_next", "avoid"],
                    "properties": {
                        "do_now": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
                        "do_next": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
                        "avoid": {"type": "array", "items": {"type": "string"}, "maxItems": 5}
                    }
                },

                # ✅ 메시지 예시: 구조 고정
                "message_examples": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["tone", "text", "when_to_send"],
                        "properties": {
                            "tone": {"type": "string", "enum": ["soft", "direct"]},
                            "text": {"type": "string"},
                            "when_to_send": {"type": "string"}
                        }
                    }
                },

                "follow_up_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 3
                },

                # ✅ patch는 서버에서 필터링도 하지만, 스키마에서도 제한
                "updated_traits_patch": {
  "type": "array",
  "maxItems": 20,
  "items": {
    "type": "object",
    "additionalProperties": False,
    "required": ["path", "value_json"],
    "properties": {
      "path": {
        "type": "string",
        "pattern": "^(user|partner|context|signals)(\\.[a-zA-Z0-9_]+){1,8}$"
      },
      "value_json": {
        "type": "string",
        "description": "JSON.stringify(value) 결과 문자열"
      }
    }
  }
},

                "confidence": {"type": "number", "minimum": 0, "maximum": 1},

                "reality_check": {"type": "string"},
                "comfort": {"type": "string"},
                "disclaimer": {"type": "string"}
            }
        }
    }
}

# ==========================
# LLM 호출
# ==========================

def call_llm_chat(req: ChatRequest) -> ChatResponse:
    merged_traits = merge_traits(req)
    instructions = build_instructions(req, merged_traits)
    input_items = to_responses_input(req.messages)

    resp = client.responses.create(
    model=MODEL,
    instructions=instructions,
    input=input_items,
    text={
        "format": {
            "type": "json_schema",
            "name": "chat_response",   # ✅ 여기로 올라와야 함
            "schema": CHAT_SCHEMA,     # ✅ 여기로 올라와야 함
            "strict": True             # ✅ 여기로 올라와야 함
        }
    },
    temperature=0.7,
    max_output_tokens=1000,
)

    raw = resp.output_text
    data = json.loads(raw)
    analysis = data.get("analysis_json") or {}
    patch = analysis.get("updated_traits_patch")
    analysis["updated_traits_patch"] = filter_updated_traits_patch(patch)
    data["analysis_json"] = analysis

    return ChatResponse.model_validate(data)


# ==========================
# ENDPOINT
# ==========================

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    for _ in range(2):
        try:
            return call_llm_chat(req)
        except (ValidationError, json.JSONDecodeError):
            continue
        except Exception as e:
            return {
                "assistant_message": f"에러 발생: {str(e)}",
                "analysis_json": {}
            }

    return {
        "assistant_message": "응답 생성 실패",
        "analysis_json": {}
    }
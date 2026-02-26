import sqlite3
import json
from pathlib import Path

DB_PATH = Path("rules.db")

REL_TYPE_RULES = [
    ("romantic_interest", "썸", [
        "상호 기대치가 명확하지 않다. 단정하지 말 것.",
        "의무/책임은 낮다. 요구보다 관찰을 우선.",
        "반복되는 행동 패턴으로 판단한다.",
        "과몰입 방지 톤을 유지한다.",
        "확신 요구는 역효과가 될 수 있음을 안내한다."
    ]),
    ("romantic_relationship", "연인", [
        "감정적 책임이 존재한다.",
        "반복 행동의 변화가 핵심 신호다.",
        "기대치 정렬(연락/표현/약속)이 중요하다.",
        "갈등 해결 방식이 관계 품질을 좌우한다.",
        "단정 대신 확인 질문을 권장한다."
    ]),
    ("coworker_peer", "동료", [
        "업무 맥락이 최우선이다.",
        "감정보다 역할/성과가 우선될 수 있다.",
        "개인 감정 해석은 신중해야 한다.",
        "업무 스트레스/일정 영향 고려.",
        "기대치(연락/반응)를 낮추는 안내."
    ]),
]

REL_STATE_RULES = [
    ("exploring", "탐색", [
        "패턴 표본이 적다. 단정 금지.",
        "반복 행동을 관찰하라고 안내.",
        "감정 확인은 부드럽게 1회 정도.",
        "과잉 해석을 줄이는 톤 유지."
    ]),
    ("stable", "안정", [
        "안정 패턴이 존재한다.",
        "변화가 핵심 신호가 될 수 있다.",
        "기존 신뢰 기반을 전제로 해석한다.",
        "직접 대화는 효과적일 수 있다."
    ]),
    ("distancing", "거리두는 중", [
        "거리두기 원인은 다층적이다.",
        "에너지/우선순위/감정 변화 구분.",
        "확인 질문은 1회만 권장.",
        "자존감 보호 톤을 유지한다."
    ]),
]

MBTI_PROFILES = [
  {
    "type": "ISTP",
    "nickname": "조용한 해결사",
    "core_drives": ["자율성 유지", "불필요한 감정 소모 최소화", "실제 행동으로 증명", "문제 해결 중심 사고"],
    "energy_management": {
      "social_energy_capacity": "low_to_medium",
      "needs_recharge_after_interaction": True,
      "prefers_one_on_one_over_group": True
    },
    "communication": {
      "response_speed_expectation": "low",
      "emotion_expression": 2,
      "directness": 4,
      "verbal_affection_level": 1,
      "action_affection_level": 4,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "situational",
      "prioritizes_logic_over_emotion": True,
      "expresses_concern_through_action": True
    },
    "conflict_pattern": {
      "initial_reaction": "withdraw",
      "after_cooling": "fix_or_solve",
      "dislikes_emotional_pressure": True
    },
    "relationship_patterns": {
      "commitment_ramp": "slow",
      "shows_interest_through": ["행동", "시간 투자", "실질적 도움"],
      "response_to_clinginess": "distance_increase",
      "jealousy_expression": "internalized"
    },
    "common_misinterpretations": [
      "표현이 적어서 무관심으로 오해받을 수 있음",
      "감정 공감이 부족하다고 보일 수 있음"
    ],
    "healthy_signals": ["필요할 때 실질적으로 도와줌", "말은 적어도 약속은 지킴", "문제 상황에서 책임감 있게 행동"],
    "unhealthy_signals": ["지속적인 연락 회피", "상대 감정을 조롱하거나 무시", "책임 회피"]
  },
  {
    "type": "ISTJ",
    "nickname": "청렴결백한 논리주의자",
    "core_drives": ["책임감 유지", "예측 가능한 안정성", "원칙과 약속 준수", "효율적 문제 해결"],
    "energy_management": {
      "social_energy_capacity": "medium",
      "needs_recharge_after_interaction": True,
      "prefers_one_on_one_over_group": True
    },
    "communication": {
      "response_speed_expectation": "medium",
      "emotion_expression": 2,
      "directness": 4,
      "verbal_affection_level": 1,
      "action_affection_level": 4,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "deliberate",
      "prioritizes_logic_over_emotion": True,
      "expresses_concern_through_action": True
    },
    "conflict_pattern": {
      "initial_reaction": "state_fact",
      "after_cooling": "structured_solution",
      "dislikes_emotional_overreaction": True
    },
    "relationship_patterns": {
      "commitment_ramp": "steady",
      "shows_interest_through": ["책임감 있는 행동", "약속 이행", "실질적 지원"],
      "response_to_clinginess": "structured_boundary",
      "jealousy_expression": "controlled"
    },
    "common_misinterpretations": [
      "차갑고 감정이 없다고 오해받기 쉬움",
      "표현이 적어서 관심이 없어 보일 수 있음"
    ],
    "healthy_signals": ["한번 맡은 관계는 쉽게 포기하지 않음", "말보다 행동으로 일관성 유지"],
    "unhealthy_signals": ["지나치게 통제적 태도", "감정 무시 및 경직된 태도"]
  },
  {
    "type": "ISFJ",
    "nickname": "용감한 수호자",
    "core_drives": ["관계의 안정과 조화", "상대의 필요를 챙김", "정서적 안전감 유지", "책임감 있는 헌신"],
    "energy_management": {
      "social_energy_capacity": "medium",
      "needs_recharge_after_interaction": True,
      "prefers_one_on_one_over_group": True
    },
    "communication": {
      "response_speed_expectation": "medium",
      "emotion_expression": 3,
      "directness": 2,
      "verbal_affection_level": 3,
      "action_affection_level": 4,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "considerate",
      "prioritizes_logic_over_emotion": False,
      "expresses_concern_through_action": True
    },
    "conflict_pattern": {
      "initial_reaction": "avoid_to_keep_harmony",
      "after_cooling": "express_hurt_indirectly",
      "dislikes_direct_confrontation": True
    },
    "relationship_patterns": {
      "commitment_ramp": "steady",
      "shows_interest_through": ["세심한 배려", "기억력 기반 챙김", "일상적 도움"],
      "response_to_clinginess": "overgive_then_exhaust",
      "jealousy_expression": "internalized"
    },
    "common_misinterpretations": [
      "괜찮다고 말하지만 속으로 상처가 누적될 수 있음",
      "배려를 당연하게 여기면 서운함이 쌓임"
    ],
    "healthy_signals": ["지속적이고 안정적인 관심 표현", "작은 디테일을 기억하고 챙김"],
    "unhealthy_signals": ["자기희생 과도", "속마음 숨기다 폭발"]
  },
  {
    "type": "INFJ",
    "nickname": "선의의 옹호자",
    "core_drives": ["의미 있는 관계 추구", "정서적 깊이와 진정성", "타인의 감정 이해", "장기적 연결"],
    "energy_management": {
      "social_energy_capacity": "low_to_medium",
      "needs_recharge_after_interaction": True,
      "prefers_one_on_one_over_group": True
    },
    "communication": {
      "response_speed_expectation": "medium",
      "emotion_expression": 3,
      "directness": 2,
      "verbal_affection_level": 3,
      "action_affection_level": 3,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "reflective",
      "prioritizes_values_over_logic": True,
      "expresses_concern_through_empathy": True
    },
    "conflict_pattern": {
      "initial_reaction": "internalize_and_reflect",
      "after_cooling": "calm_honest_conversation",
      "dislikes_superficial_resolution": True
    },
    "relationship_patterns": {
      "commitment_ramp": "slow_but_intense",
      "shows_interest_through": ["깊은 대화", "미묘한 감정 배려", "상대의 미래까지 고려"],
      "response_to_clinginess": "feel_overwhelmed_if_surface_level",
      "jealousy_expression": "quiet_but_deep"
    },
    "common_misinterpretations": [
      "혼자만의 생각이 많아 거리두는 것처럼 보일 수 있음",
      "감정 표현이 부족해 보일 수 있음",
      "상처를 쉽게 받는 예민한 사람처럼 보일 수 있음"
    ],
    "healthy_signals": ["상대의 작은 변화까지 기억하고 배려함", "진지한 대화를 시도함", "관계를 쉽게 소비하지 않음"],
    "unhealthy_signals": ["속마음을 계속 숨김", "실망이 누적되면 갑작스러운 거리두기", "과도한 자기희생"]
  },
  {
    "type": "INTJ",
    "nickname": "용의주도한 전략가",
    "core_drives": ["장기적 효율과 성장", "독립성 유지", "논리적 일관성", "감정보다 구조"],
    "energy_management": {
      "social_energy_capacity": "low_to_medium",
      "needs_recharge_after_interaction": True,
      "prefers_one_on_one_over_group": True
    },
    "communication": {
      "response_speed_expectation": "medium",
      "emotion_expression": 1,
      "directness": 4,
      "verbal_affection_level": 1,
      "action_affection_level": 3,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "highly_deliberate",
      "prioritizes_logic_over_emotion": True,
      "expresses_concern_through_solution": True
    },
    "conflict_pattern": {
      "initial_reaction": "analyze_silently",
      "after_cooling": "state_conclusion_directly",
      "dislikes_emotional_overflow": True
    },
    "relationship_patterns": {
      "commitment_ramp": "slow_but_deep",
      "shows_interest_through": ["장기 계획 공유", "문제 해결 제안", "시간 투자"],
      "response_to_clinginess": "increase_distance",
      "jealousy_expression": "internalized"
    },
    "common_misinterpretations": [
      "차갑고 감정이 없다고 보일 수 있음",
      "답이 명확하지 않으면 무관심처럼 보일 수 있음"
    ],
    "healthy_signals": ["관계를 장기 계획에 포함시킴", "문제 발생 시 해결 방안 제시"],
    "unhealthy_signals": ["지속적인 정서 무시", "상대를 논리적으로만 평가"]
  },
  {
    "type": "ISFP",
    "nickname": "호기심 많은 예술가",
    "core_drives": ["자유로운 감정 흐름", "현재의 경험 중시", "자기 진정성 유지", "부드러운 관계"],
    "energy_management": {
      "social_energy_capacity": "medium",
      "needs_recharge_after_interaction": True,
      "prefers_small_group": True
    },
    "communication": {
      "response_speed_expectation": "variable",
      "emotion_expression": 3,
      "directness": 2,
      "verbal_affection_level": 3,
      "action_affection_level": 3,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "situational",
      "prioritizes_emotion_over_logic": True,
      "expresses_concern_through_presence": True
    },
    "conflict_pattern": {
      "initial_reaction": "withdraw_emotionally",
      "after_cooling": "soft_expression",
      "dislikes_harsh_confrontation": True
    },
    "relationship_patterns": {
      "commitment_ramp": "slow_but_emotional",
      "shows_interest_through": ["함께하는 시간", "공감", "감정 공유"],
      "response_to_clinginess": "feel_overwhelmed",
      "jealousy_expression": "silent_hurt"
    },
    "common_misinterpretations": [
      "우유부단해 보일 수 있음",
      "감정 변화가 잦다고 오해받을 수 있음"
    ],
    "healthy_signals": ["함께 있을 때 집중도 높음", "작은 감정 변화를 세심히 반응"],
    "unhealthy_signals": ["갈등 회피 지속", "감정 차단 후 갑작스러운 거리두기"]
  },
  {
    "type": "INFP",
    "nickname": "열정적인 중재자",
    "core_drives": ["진정성 있는 관계", "자기 가치와 일치", "깊은 감정 교류", "이상적 연결"],
    "energy_management": {
      "social_energy_capacity": "low",
      "needs_recharge_after_interaction": True,
      "prefers_one_on_one": True
    },
    "communication": {
      "response_speed_expectation": "variable",
      "emotion_expression": 4,
      "directness": 2,
      "verbal_affection_level": 4,
      "action_affection_level": 2,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "emotion_guided",
      "prioritizes_values_over_logic": True,
      "expresses_concern_through_words": True
    },
    "conflict_pattern": {
      "initial_reaction": "internalize",
      "after_cooling": "emotional_expression",
      "dislikes_criticism": True
    },
    "relationship_patterns": {
      "commitment_ramp": "slow_but_intense",
      "shows_interest_through": ["감정 공유", "깊은 대화", "의미 있는 메시지"],
      "response_to_clinginess": "feel_pressure",
      "jealousy_expression": "internal_conflict"
    },
    "common_misinterpretations": [
      "현실감각 부족으로 보일 수 있음",
      "예민하고 상처받기 쉬워 보일 수 있음"
    ],
    "healthy_signals": ["감정을 솔직하게 나눔", "상대 가치관 존중"],
    "unhealthy_signals": ["이상과 현실 괴리로 실망 반복", "감정적 과몰입 후 갑작스런 거리두기"]
  },
  {
    "type": "INTP",
    "nickname": "논리적인 사색가",
    "core_drives": ["이해와 분석", "지적 독립성", "아이디어 탐색", "논리적 일관성"],
    "energy_management": {
      "social_energy_capacity": "low",
      "needs_recharge_after_interaction": True,
      "prefers_one_on_one": True
    },
    "communication": {
      "response_speed_expectation": "low",
      "emotion_expression": 1,
      "directness": 3,
      "verbal_affection_level": 1,
      "action_affection_level": 2,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "analytical",
      "prioritizes_logic_over_emotion": True,
      "expresses_concern_through_explanation": True
    },
    "conflict_pattern": {
      "initial_reaction": "analyze_detached",
      "after_cooling": "logical_discussion",
      "dislikes_emotional_pressure": True
    },
    "relationship_patterns": {
      "commitment_ramp": "very_slow",
      "shows_interest_through": ["지적 교류", "아이디어 공유"],
      "response_to_clinginess": "withdraw",
      "jealousy_expression": "minimal_visible"
    },
    "common_misinterpretations": [
      "무관심해 보일 수 있음",
      "감정이 없는 사람처럼 보일 수 있음"
    ],
    "healthy_signals": ["관심 분야 공유", "시간을 들여 설명함"],
    "unhealthy_signals": ["감정 완전 차단", "대화 회피"]
  },
  {
    "type": "ESTP",
    "nickname": "모험을 즐기는 사업가",
    "core_drives": ["즉각적 경험", "현실적 해결", "자유로운 선택", "지루함 회피"],
    "energy_management": {
      "social_energy_capacity": "high",
      "needs_recharge_after_interaction": False,
      "prefers_group_over_one_on_one": True
    },
    "communication": {
      "response_speed_expectation": "high_when_interested",
      "emotion_expression": 3,
      "directness": 4,
      "verbal_affection_level": 2,
      "action_affection_level": 4,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "impulsive",
      "prioritizes_present_moment": True,
      "expresses_concern_through_action": True
    },
    "conflict_pattern": {
      "initial_reaction": "confront_or_deflect",
      "after_cooling": "move_on_quickly",
      "dislikes_overanalysis": True
    },
    "relationship_patterns": {
      "commitment_ramp": "fast_if_excited",
      "shows_interest_through": ["함께 활동", "즉각적인 연락", "직접적인 스킨십/표현"],
      "response_to_clinginess": "avoid_if_bored",
      "jealousy_expression": "direct_or_playful"
    },
    "common_misinterpretations": [
      "가벼워 보일 수 있음",
      "감정 깊이가 부족하다고 오해받을 수 있음"
    ],
    "healthy_signals": ["시간과 행동을 적극적으로 투자", "위기 상황에서 즉각적으로 도움"],
    "unhealthy_signals": ["관심 식으면 급격한 거리두기", "책임 회피"]
  },
  {
    "type": "ESFP",
    "nickname": "자유로운 영혼의 연예인",
    "core_drives": ["즐거움 공유", "정서적 교류", "즉흥적 경험", "타인의 반응"],
    "energy_management": {
      "social_energy_capacity": "high",
      "needs_recharge_after_interaction": False,
      "prefers_group_over_one_on_one": True
    },
    "communication": {
      "response_speed_expectation": "high",
      "emotion_expression": 5,
      "directness": 3,
      "verbal_affection_level": 5,
      "action_affection_level": 4,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "emotionally_impulsive",
      "prioritizes_emotion_over_logic": True,
      "expresses_concern_through_presence": True
    },
    "conflict_pattern": {
      "initial_reaction": "emotional_expression",
      "after_cooling": "seek_reconnection",
      "dislikes_emotional_distance": True
    },
    "relationship_patterns": {
      "commitment_ramp": "fast_if_emotionally_engaged",
      "shows_interest_through": ["잦은 연락", "감정 표현", "함께하는 활동"],
      "response_to_clinginess": "reciprocate_initially",
      "jealousy_expression": "visible"
    },
    "common_misinterpretations": [
      "가볍고 깊이가 없다고 오해받을 수 있음",
      "감정 기복이 심해 보일 수 있음"
    ],
    "healthy_signals": ["관계를 즐겁게 유지하려 노력", "감정 솔직히 표현"],
    "unhealthy_signals": ["감정 과잉 후 갑작스런 회피", "주목 받지 못하면 관심 감소"]
  },
  {
    "type": "ENFP",
    "nickname": "재기발랄한 활동가",
    "core_drives": ["새로운 가능성 탐색", "정서적 연결", "자유로운 표현", "의미 있는 관계"],
    "energy_management": {
      "social_energy_capacity": "high_but_fluctuating",
      "needs_recharge_after_intense_emotion": True,
      "prefers_dynamic_interaction": True
    },
    "communication": {
      "response_speed_expectation": "variable",
      "emotion_expression": 5,
      "directness": 3,
      "verbal_affection_level": 5,
      "action_affection_level": 3,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "idea_driven",
      "prioritizes_emotion_and_possibility": True,
      "expresses_concern_through_words": True
    },
    "conflict_pattern": {
      "initial_reaction": "emotional_outburst_or_reflection",
      "after_cooling": "deep_conversation",
      "dislikes_being_controlled": True
    },
    "relationship_patterns": {
      "commitment_ramp": "fast_but_reassess_later",
      "shows_interest_through": ["장문 메시지", "미래 이야기", "감정 표현"],
      "response_to_clinginess": "feel_conflicted",
      "jealousy_expression": "emotional"
    },
    "common_misinterpretations": [
      "감정이 과장되어 보일 수 있음",
      "처음엔 뜨겁지만 식는 것처럼 보일 수 있음"
    ],
    "healthy_signals": ["미래를 함께 상상", "깊은 감정 대화 시도"],
    "unhealthy_signals": ["흥미 잃으면 급격한 연락 감소", "감정 기복 심화"]
  },
  {
    "type": "ENTP",
    "nickname": "뜨거운 논쟁을 즐기는 변론가",
    "core_drives": ["지적 자극", "새로운 관점 탐색", "자율성", "변화와 도전"],
    "energy_management": {
      "social_energy_capacity": "high",
      "needs_recharge_after_boredom": True,
      "prefers_dynamic_group": True
    },
    "communication": {
      "response_speed_expectation": "variable",
      "emotion_expression": 2,
      "directness": 4,
      "verbal_affection_level": 2,
      "action_affection_level": 3,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "idea_experimenting",
      "prioritizes_logic_over_emotion": True,
      "expresses_concern_through_argument": True
    },
    "conflict_pattern": {
      "initial_reaction": "debate",
      "after_cooling": "intellectual_resolution",
      "dislikes_emotional_restriction": True
    },
    "relationship_patterns": {
      "commitment_ramp": "slow_until_stimulated",
      "shows_interest_through": ["지적 대화", "아이디어 공유", "유머"],
      "response_to_clinginess": "distance_increase",
      "jealousy_expression": "hidden_or_rationalized"
    },
    "common_misinterpretations": [
      "논쟁을 싸움으로 오해받을 수 있음",
      "감정이 부족해 보일 수 있음"
    ],
    "healthy_signals": ["깊은 토론을 이어감", "지적 관심 유지"],
    "unhealthy_signals": ["상대를 논리로 압박", "지루해지면 급격한 관심 저하"]
  },
  {
    "type": "ESTJ",
    "nickname": "엄격한 관리자",
    "core_drives": ["효율과 결과", "명확한 역할 분담", "책임 있는 구조", "통제 가능한 질서"],
    "energy_management": {
      "social_energy_capacity": "high",
      "needs_recharge_after_interaction": False,
      "prefers_group_over_one_on_one": True
    },
    "communication": {
      "response_speed_expectation": "high",
      "emotion_expression": 2,
      "directness": 5,
      "verbal_affection_level": 1,
      "action_affection_level": 3,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "decisive",
      "prioritizes_logic_over_emotion": True,
      "expresses_concern_through_action": True
    },
    "conflict_pattern": {
      "initial_reaction": "confront",
      "after_cooling": "clarify_rules",
      "dislikes_indecision": True
    },
    "relationship_patterns": {
      "commitment_ramp": "fast_if_clear",
      "shows_interest_through": ["책임 분담", "현실적 도움"],
      "response_to_clinginess": "push_for_independence",
      "jealousy_expression": "direct"
    },
    "common_misinterpretations": [
      "지배적이고 차갑게 보일 수 있음",
      "감정 배려가 부족해 보일 수 있음"
    ],
    "healthy_signals": ["명확한 기준 제시", "책임감 있는 행동"],
    "unhealthy_signals": ["지나친 통제", "상대 감정 무시"]
  },
  {
    "type": "ESFJ",
    "nickname": "사교적인 외교관",
    "core_drives": ["관계 유지", "안정과 소속감", "정서적 교류", "타인의 만족"],
    "energy_management": {
      "social_energy_capacity": "high",
      "needs_recharge_after_interaction": False,
      "prefers_group_over_one_on_one": True
    },
    "communication": {
      "response_speed_expectation": "high",
      "emotion_expression": 4,
      "directness": 3,
      "verbal_affection_level": 4,
      "action_affection_level": 3,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "emotionally_considerate",
      "prioritizes_logic_over_emotion": False,
      "expresses_concern_through_action": True
    },
    "conflict_pattern": {
      "initial_reaction": "seek_reassurance",
      "after_cooling": "talk_and_restore",
      "dislikes_emotional_distance": True
    },
    "relationship_patterns": {
      "commitment_ramp": "fast_if_emotional_connection",
      "shows_interest_through": ["연락 빈도", "감정 표현", "배려 행동"],
      "response_to_clinginess": "reciprocate",
      "jealousy_expression": "visible"
    },
    "common_misinterpretations": [
      "집착으로 오해받을 수 있음",
      "관심 요구가 많아 보일 수 있음"
    ],
    "healthy_signals": ["정서적 안정감 제공", "관계 유지 노력"],
    "unhealthy_signals": ["과도한 인정 욕구", "감정적 압박"]
  },
  {
    "type": "ENFJ",
    "nickname": "정의로운 사회운동가",
    "core_drives": ["사람 간 연결 강화", "타인의 성장 지원", "정서적 조화", "영향력 있는 관계"],
    "energy_management": {
      "social_energy_capacity": "high",
      "needs_recharge_after_emotional_burnout": True,
      "prefers_group_over_one_on_one": True
    },
    "communication": {
      "response_speed_expectation": "high",
      "emotion_expression": 4,
      "directness": 3,
      "verbal_affection_level": 4,
      "action_affection_level": 4,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "people_considerate",
      "prioritizes_emotion_and_group_harmony": True,
      "expresses_concern_through_guidance": True
    },
    "conflict_pattern": {
      "initial_reaction": "seek_dialogue",
      "after_cooling": "structured_emotional_resolution",
      "dislikes_emotional_distance": True
    },
    "relationship_patterns": {
      "commitment_ramp": "fast_if_emotionally_connected",
      "shows_interest_through": ["지속적 연락", "감정 확인", "미래 계획 공유"],
      "response_to_clinginess": "initially_reassure_then_exhaust",
      "jealousy_expression": "visible_but_explained"
    },
    "common_misinterpretations": [
      "지나치게 관여한다고 보일 수 있음",
      "감정 과잉으로 오해받을 수 있음"
    ],
    "healthy_signals": ["갈등 시 먼저 대화 시도", "상대의 감정 변화를 빠르게 캐치", "관계를 장기적으로 계획"],
    "unhealthy_signals": ["과도한 통제(좋은 의도지만 강요)", "상대의 독립성 침해", "감정 소진 후 갑작스런 냉각"]
  },
  {
    "type": "ENTJ",
    "nickname": "대담한 통솔자",
    "core_drives": ["목표 달성", "효율적 구조 구축", "결과 중심 사고", "영향력 행사"],
    "energy_management": {
      "social_energy_capacity": "high",
      "needs_recharge_after_failure": True,
      "prefers_group_lead_role": True
    },
    "communication": {
      "response_speed_expectation": "high",
      "emotion_expression": 2,
      "directness": 5,
      "verbal_affection_level": 1,
      "action_affection_level": 3,
      "scale_1to5_note": "1=매우 낮음, 5=매우 높음"
    },
    "decision_style": {
      "impulse_vs_deliberate": "decisive_and_future_oriented",
      "prioritizes_logic_over_emotion": True,
      "expresses_concern_through_strategy": True
    },
    "conflict_pattern": {
      "initial_reaction": "confront_directly",
      "after_cooling": "clarify_structure",
      "dislikes_indecision": True
    },
    "relationship_patterns": {
      "commitment_ramp": "fast_if_aligned_goals",
      "shows_interest_through": ["미래 계획 포함", "책임 공유", "현실적 지원"],
      "response_to_clinginess": "encourage_independence",
      "jealousy_expression": "controlled_or_logical"
    },
    "common_misinterpretations": [
      "차갑고 권위적으로 보일 수 있음",
      "감정 배려가 부족하다고 오해받을 수 있음"
    ],
    "healthy_signals": ["관계를 목표 계획에 포함", "위기 상황에서 책임감 있게 리드", "명확한 의사 표현"],
    "unhealthy_signals": ["지나친 통제와 지시", "상대 감정 경시", "성과 중심으로 관계 평가"]
  }
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 테이블 생성
    cur.execute("""
    CREATE TABLE IF NOT EXISTS relationship_type_modifiers (
        type_code TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        rules_json TEXT NOT NULL,
        prompt_hint TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        is_active INTEGER NOT NULL DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS relationship_state_modifiers (
        state_code TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        rules_json TEXT NOT NULL,
        prompt_hint TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        is_active INTEGER NOT NULL DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS mbti_profiles (
        mbti TEXT PRIMARY KEY,
        profile_json TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1,
        is_active INTEGER NOT NULL DEFAULT 1
    );
    """)

    # upsert(간단하게 delete 후 insert로)
    for code, name, rules in REL_TYPE_RULES:
        cur.execute("DELETE FROM relationship_type_modifiers WHERE type_code=?", (code,))
        cur.execute("""
        INSERT INTO relationship_type_modifiers(type_code, display_name, rules_json, prompt_hint, version, is_active)
        VALUES (?, ?, ?, ?, 1, 1)
        """, (code, name, json.dumps({"rules": rules}, ensure_ascii=False), None))

    for code, name, rules in REL_STATE_RULES:
        cur.execute("DELETE FROM relationship_state_modifiers WHERE state_code=?", (code,))
        cur.execute("""
        INSERT INTO relationship_state_modifiers(state_code, display_name, rules_json, prompt_hint, version, is_active)
        VALUES (?, ?, ?, ?, 1, 1)
        """, (code, name, json.dumps({"rules": rules}, ensure_ascii=False), None))

    for prof in MBTI_PROFILES:
        mbti = prof["type"].upper()
        cur.execute("DELETE FROM mbti_profiles WHERE mbti=?", (mbti,))
        cur.execute("""
        INSERT INTO mbti_profiles(mbti, profile_json, version, is_active)
        VALUES (?, ?, 1, 1)
        """, (mbti, json.dumps(prof, ensure_ascii=False)))

    conn.commit()
    conn.close()
    print(f"✅ DB initialized: {DB_PATH.resolve()}")

if __name__ == "__main__":
    main()
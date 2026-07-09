"""Canonical 5-question interview schema.

The order, text, and validation thresholds of these questions are the product
surface. Reordering or rewording is a product change, not a refactor.
"""
from __future__ import annotations

from typing import Any


QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "what-who-where",
        "prompt": "무엇을, 누가, 어떤 상황에서 쓰나요?",
        "answer_type": "text",
        "choices": [],
        "min_length": 20,
        "validation_hint": "20자 이상의 한국어/영문 설명 (대상 사용자, 사용 맥락 포함)",
    },
    {
        "id": "why-this-problem",
        "prompt": "왜 이 문제를 선택했나요?",
        "answer_type": "text",
        "choices": [],
        "min_length": 20,
        "validation_hint": "20자 이상 — 해결하려는 문제의 동기와 임팩트",
    },
    {
        "id": "how-it-works",
        "prompt": "플러그인은 어떻게 작동하나요?",
        "answer_type": "text",
        "choices": [],
        "min_length": 20,
        "validation_hint": "20자 이상 — 입력/처리/출력 흐름을 한 단락으로",
    },
    {
        "id": "ai-usage",
        "prompt": "AI를 어떻게 활용했나요?",
        "answer_type": "text",
        "choices": [],
        "min_length": 20,
        "validation_hint": "20자 이상 — 어떤 AI 호출이 어느 단계에서 사용되는지",
    },
    {
        "id": "how-verified",
        "prompt": "어떻게 검증했나요?",
        "answer_type": "text",
        "choices": [],
        "min_length": 20,
        "validation_hint": "20자 이상 — 테스트/시나리오/수동 검증 방법",
    },
]


_CANONICAL_IDS: tuple[str, ...] = tuple(q["id"] for q in QUESTIONS)
_QUESTION_BY_ID: dict[str, dict[str, Any]] = {q["id"]: q for q in QUESTIONS}


def get_question(qid: str) -> dict[str, Any]:
    """Return the question dict for a given id, or raise KeyError."""
    return _QUESTION_BY_ID[qid]


def canonical_ids() -> tuple[str, ...]:
    """Return the canonical question id sequence (read-only)."""
    return _CANONICAL_IDS

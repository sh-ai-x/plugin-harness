"""Canonical 5-question interview schema (SSOT for the harness interview surface).

The order and prompts are LOCKED per phases/0-mvp/step0.md. Reorder is a product change.
"""

QUESTIONS: list[dict] = [
    {
        "id": "what-who-where",
        "prompt": "무엇을, 누가, 어떤 상황에서 쓰나요?",
        "answer_type": "text",
        "choices": None,
        "min_length": 20,
        "validation_hint": "describe the user, the situation, and what they are doing",
    },
    {
        "id": "why-this-problem",
        "prompt": "왜 이 문제를 선택했나요?",
        "answer_type": "text",
        "choices": None,
        "min_length": 20,
        "validation_hint": "explain the pain point and why now",
    },
    {
        "id": "how-it-works",
        "prompt": "플러그인은 어떻게 작동하나요?",
        "answer_type": "text",
        "choices": None,
        "min_length": 20,
        "validation_hint": "describe the runtime flow step by step",
    },
    {
        "id": "ai-usage",
        "prompt": "AI를 어떻게 활용했나요?",
        "answer_type": "text",
        "choices": None,
        "min_length": 20,
        "validation_hint": "explain how AI is invoked and what it produces",
    },
    {
        "id": "how-verified",
        "prompt": "어떻게 검증했나요?",
        "answer_type": "text",
        "choices": None,
        "min_length": 20,
        "validation_hint": "describe the verification approach (tests, scenarios, manual checks)",
    },
]
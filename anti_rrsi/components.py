# Copyright 2026 Antigravity Research & Autonomous Engineering Org
# Licensed under Apache 2.0.

from __future__ import annotations

import re
from typing import Sequence

K_ALL = [
    "prompt",
    "control_flow",
    "config",
    "output_plumbing",
    "context_mgmt",
    "client_tool",
    "skill",
    "memory",
    "subagent",
]

K_STR = ["client_tool", "skill", "memory", "subagent"]

GENERIC_SIGNALS = [
    ("memory", [r"\bMemory\(", r"\.remember\(", r"\.recall\(", r"_STATE_DIR"]),
    ("skill", [r"skills/", r"SkillRegistry", r"skill_use", r"skill_catalog", r"upload_skills"]),
    ("client_tool", [r"ToolRegistry", r"register_tool", r"tool_spec", r"CLIENT_TOOLS"]),
    ("subagent", [r"\bsubcall\(", r"sub_agent", r"subagent"]),
    ("config", [r"\.json\b", r"\.toml\b", r"\.yaml\b", r"MAX_TURNS", r"TEMPERATURE"]),
    ("control_flow", [r"\bwhile\b", r"\bretry\b", r"\bfor\b", r"\bif\b", r"except\b"]),
]

_STRING_LINE = re.compile(r'^[+-]\s*(?:[frb]?["\']|""")')


def is_text_only(diff: str) -> bool:
    """True when every altered line is string literal, comment, or prose."""
    changed = [
        line for line in diff.splitlines()
        if (line.startswith("+") or line.startswith("-"))
        and not line.startswith("+++")
        and not line.startswith("---")
        and line[1:].strip()
    ]
    if not changed:
        return False
    return all(_STRING_LINE.match(l) or l[1:].lstrip().startswith("#") for l in changed)


def classify_diff(diff: str, domain_signals: Sequence[tuple[str, list[str]]] | None = None) -> str:
    """Classify diff into one of K_ALL component tags."""
    if is_text_only(diff):
        return "prompt"
    all_signals = list(domain_signals or []) + GENERIC_SIGNALS
    for comp, pats in all_signals:
        if any(re.search(p, diff) for p in pats):
            return comp
    return "prompt"


def estimate_token_count(text: str) -> int:
    """Estimate token count using 4 chars per token rule of thumb."""
    if not text:
        return 0
    return max(1, len(text) // 4)

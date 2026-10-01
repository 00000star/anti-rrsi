# Copyright 2026 Antigravity Research & Autonomous Engineering Org
# Licensed under Apache 2.0.

"""Null-Space Pruner: Negative-space optimization for agent harnesses.

Formulation:
    minimize    C(H')
    subject to  S(H') >= S(H_t) - delta_tol
                H' is a sub-graph / subset of H_t (pure deletion/simplification)

Identifies cargo-cult prompting, inert helper functions, dead skills, and
redundant tool definitions, shrinking context footprint without regressing
benchmark competence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Sequence

from .components import estimate_token_count
from .config import AntiRRSIConfig


@dataclass
class PruneCandidate:
    component: str
    target_identifier: str       # section name, function name, or line range
    original_snippet: str
    pruned_snippet: str
    token_delta: int              # negative integer (tokens removed)
    diff: str = ""

    @property
    def token_reduction(self) -> int:
        return abs(min(0, self.token_delta))


@dataclass
class PruneResult:
    accepted: bool
    initial_score: float
    final_score: float
    initial_cost: float
    final_cost: float
    delta_S: float
    delta_C: float
    pruned_components: list[PruneCandidate] = field(default_factory=list)
    reason: str = ""

    @property
    def compression_ratio(self) -> float:
        if self.initial_cost <= 0:
            return 0.0
        return (self.initial_cost - self.final_cost) / self.initial_cost


class NullSpacePruner:
    """Discovers and validates candidate deletions in an agent harness."""

    def __init__(self, config: AntiRRSIConfig | None = None):
        self.cfg = config or AntiRRSIConfig()

    def identify_candidates(self, harness_text: str, component_type: str = "prompt") -> list[PruneCandidate]:
        """Parse harness content and propose structured deletion blocks."""
        candidates = []

        if component_type == "prompt":
            # Identify markdown sections, bullet items, and verbose admonitions
            sections = re.split(r"(?m)(^#{1,4}\s+[^\n]+)", harness_text)
            # Reconstruct pairs
            for i in range(1, len(sections), 2):
                header = sections[i]
                body = sections[i + 1] if i + 1 < len(sections) else ""
                full_block = header + body
                tokens = estimate_token_count(full_block)
                if tokens > 15:  # worth pruning
                    candidates.append(PruneCandidate(
                        component="prompt",
                        target_identifier=header.strip("# \t\r\n"),
                        original_snippet=full_block,
                        pruned_snippet="",
                        token_delta=-tokens,
                        diff=f"- {header.strip()}\n- [pruned {tokens} tokens body]"
                    ))

            # Also identify bullet points
            bullet_pattern = re.compile(r"(?m)^\s*[-*]\s+.{30,}$")
            for match in bullet_pattern.finditer(harness_text):
                bullet = match.group(0)
                tokens = estimate_token_count(bullet)
                candidates.append(PruneCandidate(
                    component="prompt",
                    target_identifier=bullet[:35] + "...",
                    original_snippet=bullet,
                    pruned_snippet="",
                    token_delta=-tokens,
                    diff=f"- {bullet}"
                ))

        elif component_type in ("client_tool", "control_flow"):
            # Identify individual function definitions or tool decorators
            func_pattern = re.compile(r"(?m)^(?:@\w+.*\n)*def\s+(\w+)\s*\([^)]*\).*?:(?:\n(?:[ \t]+.*|\s*))*")
            for match in func_pattern.finditer(harness_text):
                func_code = match.group(0)
                func_name = match.group(1)
                tokens = estimate_token_count(func_code)
                candidates.append(PruneCandidate(
                    component=component_type,
                    target_identifier=func_name,
                    original_snippet=func_code,
                    pruned_snippet="",
                    token_delta=-tokens,
                    diff=f"- def {func_name}(...)"
                ))

        return candidates

    def evaluate_pruning(
        self,
        candidate: PruneCandidate,
        eval_fn: Callable[[str], tuple[float, float]],
        current_harness: str,
        current_score: float,
        current_cost: float,
    ) -> PruneResult:
        """Apply candidate deletion, evaluate via eval_fn(harness) -> (score, cost)."""
        # Formulate candidate harness by replacing target snippet
        new_harness = current_harness.replace(candidate.original_snippet, candidate.pruned_snippet, 1)
        if new_harness == current_harness:
            return PruneResult(
                accepted=False,
                initial_score=current_score,
                final_score=current_score,
                initial_cost=current_cost,
                final_cost=current_cost,
                delta_S=0.0,
                delta_C=0.0,
                reason="Snippet not found in current harness"
            )

        new_score, new_cost = eval_fn(new_harness)
        delta_S = new_score - current_score
        delta_C = (new_cost - current_cost) / current_cost if current_cost > 0 else 0.0

        # Null-space acceptance condition:
        # Score must not regress beyond tolerance (delta_S >= -delta_tol)
        # Cost reduction must meet threshold (delta_C <= -cost_reduction_min)
        score_ok = delta_S >= -self.cfg.delta_tol
        cost_ok = delta_C <= -self.cfg.cost_reduction_min

        if score_ok and cost_ok:
            return PruneResult(
                accepted=True,
                initial_score=current_score,
                final_score=new_score,
                initial_cost=current_cost,
                final_cost=new_cost,
                delta_S=delta_S,
                delta_C=delta_C,
                pruned_components=[candidate],
                reason=f"Accepted null-space compression: dS={delta_S:+.4f} >= -{self.cfg.delta_tol}, dC={delta_C:+.2%}"
            )
        else:
            reasons = []
            if not score_ok:
                reasons.append(f"Score dropped too sharply: {delta_S:+.4f} < -{self.cfg.delta_tol}")
            if not cost_ok:
                reasons.append(f"Cost reduction insufficient: {delta_C:+.2%} > -{self.cfg.cost_reduction_min:.1%}")
            return PruneResult(
                accepted=False,
                initial_score=current_score,
                final_score=new_score,
                initial_cost=current_cost,
                final_cost=new_cost,
                delta_S=delta_S,
                delta_C=delta_C,
                pruned_components=[candidate],
                reason="Rejected: " + "; ".join(reasons)
            )

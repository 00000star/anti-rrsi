# Copyright 2026 Antigravity Research & Autonomous Engineering Org
# Licensed under Apache 2.0.

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class AntiRRSIConfig:
    """Hyperparameters and configuration for Anti-RRSI."""

    # Null-space pruning parameters
    delta_tol: float = 0.005              # Max acceptable score degradation during compression
    cost_reduction_min: float = 0.05       # Minimum relative token/cost reduction (-5%)
    max_prune_rounds: int = 15            # Maximum sequential pruning iterations

    # Adversarial Red-Teaming parameters
    adversarial_b_max: int = 1            # Strict L0 edit budget: single surgical disruption
    max_attack_depth: int = 5             # Max search depth for brittle-point exploration
    severity_threshold: float = 0.15      # Delta S drop required to flag a critical vulnerability

    # Reverse Planning parameters
    trace_window: int = 10                # Number of trailing interaction steps to backtrace
    confidence_threshold: float = 0.75    # Required causal confidence for backward intervention

    # Evaluator Auditing parameters
    leakage_regex_sensitivity: float = 0.90
    mock_leak_threshold: float = 0.01     # Assertions with zero variation flagged as suspicious

    # Daemon and System paths
    history_file: str = "anti_rrsi_history.jsonl"
    daemon_interval_sec: int = 60
    worktree_prefix: str = "anti_rrsi_worktree"

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> AntiRRSIConfig:
        data = json.loads(json_str)
        return cls(**data)

    def save(self, path: Path | str) -> None:
        Path(path).write_text(self.to_json())

    @classmethod
    def load(cls, path: Path | str) -> AntiRRSIConfig:
        return cls.from_json(Path(path).read_text())

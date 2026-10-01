# Copyright 2026 Antigravity Research & Autonomous Engineering Org
# Licensed under Apache 2.0.

"""Anti-RRSI: Inverse Regularized Recursive Self-Improvement.

Provides:
- NullSpacePruner: Prune dead weight and cargo-cult prompt instructions while preserving benchmark performance.
- AdversarialRedTeam: Identify sparse edits (||z_t||_0 <= 1) that expose failure modes and prompt brittle points.
- ReversePlanner: Goal-conditioned backward planning from failing tasks to surgical candidate edits.
- EvaluatorAuditor: Detect benchmark leakage, false-positive test passes, and reward gaming.
- PassiveDaemon: Background optimization daemon compatible with local Termux or cloud compute.
"""

from .config import AntiRRSIConfig
from .prune import NullSpacePruner, PruneCandidate, PruneResult
from .redteam import AdversarialRedTeam, AttackVector, RedTeamResult
from .reverse_planner import ReversePlanner, BackwardTrace, SurgicalEdit
from .auditor import EvaluatorAuditor, AuditFinding, AuditReport
from .daemon import PassiveDaemon

__version__ = "1.0.0"
__all__ = [
    "AntiRRSIConfig",
    "NullSpacePruner",
    "PruneCandidate",
    "PruneResult",
    "AdversarialRedTeam",
    "AttackVector",
    "RedTeamResult",
    "ReversePlanner",
    "BackwardTrace",
    "SurgicalEdit",
    "EvaluatorAuditor",
    "AuditFinding",
    "AuditReport",
    "PassiveDaemon",
]

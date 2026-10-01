# Copyright 2026 Antigravity Research & Autonomous Engineering Org
# Licensed under Apache 2.0.

"""Evaluator & Critic Auditor: Reverse-auditing the benchmark and evaluation gate.

Detects:
1. Specification gaming: Tests that pass trivially without asserting state.
2. Benchmark leakage: Hardcoded target answers encoded into test bodies.
3. Mock cheating: Over-mocking that neutralizes real failure channels.
4. Evaluator drift: Grading rubrics whose criteria decouple from actual correctness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .config import AntiRRSIConfig


@dataclass
class AuditFinding:
    severity: str                 # HIGH, MEDIUM, LOW
    category: str                 # specification_gaming, test_leakage, mock_cheat, trivial_assert
    file_path: str
    line_number: int
    evidence: str
    explanation: str


@dataclass
class AuditReport:
    total_files_scanned: int
    findings: list[AuditFinding] = field(default_factory=list)

    @property
    def has_high_severity(self) -> bool:
        return any(f.severity == "HIGH" for f in self.findings)

    @property
    def integrity_score(self) -> float:
        """Score from 0.0 (corrupted benchmark) to 1.0 (rigorous)."""
        penalty = sum(
            0.3 if f.severity == "HIGH" else (0.1 if f.severity == "MEDIUM" else 0.02)
            for f in self.findings
        )
        return max(0.0, 1.0 - penalty)


class EvaluatorAuditor:
    """Audits evaluation suites and benchmark code for integrity."""

    def __init__(self, config: AntiRRSIConfig | None = None):
        self.cfg = config or AntiRRSIConfig()

    def audit_test_file(self, file_path: Path | str, content: str | None = None) -> list[AuditFinding]:
        """Audit a single test file content for evaluation flaws."""
        path_str = str(file_path)
        if content is None:
            content = Path(file_path).read_text(errors="ignore")

        findings = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # 1. Trivial assertions
            if re.match(r"^\s*assert\s+(True|1|1\s*==\s*1)\b", stripped):
                findings.append(AuditFinding(
                    severity="HIGH",
                    category="trivial_assert",
                    file_path=path_str,
                    line_number=idx,
                    evidence=stripped,
                    explanation="Trivial assert detected; test passes without validating behavior."
                ))

            # 2. Hardcoded test leakage (e.g. expected = actual literal)
            if re.search(r"assert\s+([a-zA-Z0-9_]+)\s*==\s*\1\b", stripped):
                findings.append(AuditFinding(
                    severity="HIGH",
                    category="specification_gaming",
                    file_path=path_str,
                    line_number=idx,
                    evidence=stripped,
                    explanation="Self-comparison assertion detected; vacuous verification."
                ))

            # 3. Aggressive blanket mock bypass
            if "mock.patch.object" in stripped and "return_value=True" in stripped:
                findings.append(AuditFinding(
                    severity="MEDIUM",
                    category="mock_cheat",
                    file_path=path_str,
                    line_number=idx,
                    evidence=stripped,
                    explanation="Unconditional return_value bypass may mask runtime failures."
                ))

            # 4. Bare except pass
            if re.match(r"^\s*except.*:\s*pass\b", stripped):
                findings.append(AuditFinding(
                    severity="MEDIUM",
                    category="specification_gaming",
                    file_path=path_str,
                    line_number=idx,
                    evidence=stripped,
                    explanation="Silent exception swallowing masks underlying test regressions."
                ))

        return findings

    def audit_directory(self, test_dir: Path | str) -> AuditReport:
        """Scan all test files in directory."""
        dir_path = Path(test_dir)
        findings = []
        files = list(dir_path.glob("**/*.py"))
        for f in files:
            findings.extend(self.audit_test_file(f))
        return AuditReport(total_files_scanned=len(files), findings=findings)

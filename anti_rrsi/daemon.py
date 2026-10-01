# Copyright 2026 Antigravity Research & Autonomous Engineering Org
# Licensed under Apache 2.0.

"""Passive Daemon: Continuous background optimization and verification.

Operates asynchronously to:
1. Detect harness and prompt bloat across active projects.
2. Run null-space pruning in background mode.
3. Audit test files for evaluation integrity.
4. Record structured audit and pruning ledgers.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path

from .auditor import EvaluatorAuditor
from .config import AntiRRSIConfig
from .prune import NullSpacePruner


class PassiveDaemon:
    """Lightweight, non-intrusive background optimizer."""

    def __init__(self, workspace_root: Path | str, config: AntiRRSIConfig | None = None):
        self.workspace_root = Path(workspace_root)
        self.cfg = config or AntiRRSIConfig()
        self.pruner = NullSpacePruner(self.cfg)
        self.auditor = EvaluatorAuditor(self.cfg)
        self.ledger_path = self.workspace_root / self.cfg.history_file

    def record_event(self, event_type: str, data: dict) -> None:
        """Append an event to the persistent JSONL ledger."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": event_type,
            **data,
        }
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def run_pulse(self) -> dict:
        """Execute one passive inspection pulse across the workspace."""
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scanned_prompts": 0,
            "pruning_candidates_found": 0,
            "test_audit_findings": 0,
        }

        # 1. Scan for markdown prompt files (.md, GEMINI.md, system prompts)
        for md_file in self.workspace_root.glob("**/*.md"):
            if ".git" in str(md_file) or ".venv" in str(md_file):
                continue
            text = md_file.read_text(errors="ignore")
            candidates = self.pruner.identify_candidates(text, component_type="prompt")
            if candidates:
                results["scanned_prompts"] += 1
                results["pruning_candidates_found"] += len(candidates)
                self.record_event("PRUNE_OPPORTUNITY", {
                    "file": str(md_file),
                    "candidates_count": len(candidates),
                    "potential_token_savings": sum(c.token_reduction for c in candidates),
                })

        # 2. Audit test suites
        tests_dir = self.workspace_root / "tests"
        if tests_dir.exists():
            report = self.auditor.audit_directory(tests_dir)
            results["test_audit_findings"] = len(report.findings)
            self.record_event("TEST_AUDIT", {
                "total_scanned": report.total_files_scanned,
                "integrity_score": report.integrity_score,
                "findings_count": len(report.findings),
            })

        return results

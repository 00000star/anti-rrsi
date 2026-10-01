# Copyright 2026 Antigravity Research & Autonomous Engineering Org
# Licensed under Apache 2.0.

"""Reverse Planner: Backward causal planning from failed terminal states.

Formulation:
    Given target state S* (Task Pass) and observed failure trace tau_fail:
    P(Delta H | S*, tau_fail)

Back-traces causal divergence points and synthesizes direct surgical edits
instead of unstructured forward trial-and-error.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence

from .config import AntiRRSIConfig


@dataclass
class BackwardTrace:
    step_index: int
    divergence_type: str        # syntax_error, tool_call_failure, context_truncation, assertion_miss
    evidence: str
    target_component: str
    suggested_action: str


@dataclass
class SurgicalEdit:
    target_file: str
    component: str
    rationale: str
    original_block: str
    proposed_block: str
    confidence: float


class ReversePlanner:
    """Computes inverse interventions from failure traces to candidate edits."""

    def __init__(self, config: AntiRRSIConfig | None = None):
        self.cfg = config or AntiRRSIConfig()

    def analyze_failure_trace(self, trace_logs: str) -> list[BackwardTrace]:
        """Back-trace causal chain from execution logs to failure root causes."""
        traces = []

        # 1. Check for command execution errors or exit codes
        exit_code_match = re.search(r"exited with code\s+([1-9]\d*)", trace_logs)
        if exit_code_match:
            code = exit_code_match.group(1)
            traces.append(BackwardTrace(
                step_index=0,
                divergence_type="command_failure",
                evidence=f"Command exited with non-zero code {code}",
                target_component="control_flow",
                suggested_action="Wrap execution in error recovery or check prerequisite binaries."
            ))

        # 2. Check for missing module / import errors
        import_match = re.search(r"ModuleNotFoundError:\s+No module named ['\"]([^'\"]+)['\"]", trace_logs)
        if import_match:
            mod = import_match.group(1)
            traces.append(BackwardTrace(
                step_index=1,
                divergence_type="environment_miss",
                evidence=f"Missing dependency '{mod}'",
                target_component="config",
                suggested_action=f"Add '{mod}' to project dependencies or setup virtual environment."
            ))

        # 3. Check for permission errors
        if "Permission denied" in trace_logs:
            traces.append(BackwardTrace(
                step_index=2,
                divergence_type="permission_error",
                evidence="Filesystem permission denied during execution",
                target_component="control_flow",
                suggested_action="Use writable storage path (e.g. bind mounts or user-accessible space)."
            ))

        # 4. Check for JSON / format parse failures
        if "JSONDecodeError" in trace_logs or "Expecting value" in trace_logs:
            traces.append(BackwardTrace(
                step_index=3,
                divergence_type="format_parse_failure",
                evidence="Output parser failed to decode JSON response from model",
                target_component="output_plumbing",
                suggested_action="Implement robust markdown-fence stripping and fuzzy JSON extraction."
            ))

        return traces

    def synthesize_surgical_edit(
        self,
        harness_text: str,
        trace: BackwardTrace,
        target_file: str = "harness.py",
    ) -> SurgicalEdit | None:
        """Synthesize a minimal surgical edit addressing the root cause."""
        if trace.divergence_type == "format_parse_failure":
            orig = "json.loads(response)"
            repl = "json.loads(re.sub(r'```json|```', '', response).strip())"
            if orig in harness_text:
                return SurgicalEdit(
                    target_file=target_file,
                    component=trace.target_component,
                    rationale=trace.suggested_action,
                    original_block=orig,
                    proposed_block=repl,
                    confidence=0.92,
                )

        if trace.divergence_type == "permission_error":
            orig = "path = '/sdcard/'"
            repl = "path = os.getenv('STORAGE_DIR', '/tmp/')"
            if orig in harness_text:
                return SurgicalEdit(
                    target_file=target_file,
                    component=trace.target_component,
                    rationale=trace.suggested_action,
                    original_block=orig,
                    proposed_block=repl,
                    confidence=0.85,
                )

        return None

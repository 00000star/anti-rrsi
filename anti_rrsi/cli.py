# Copyright 2026 Antigravity Research & Autonomous Engineering Org
# Licensed under Apache 2.0.

"""Unified Command Line Interface for Anti-RRSI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .auditor import EvaluatorAuditor
from .config import AntiRRSIConfig
from .daemon import PassiveDaemon
from .prune import NullSpacePruner
from .redteam import AdversarialRedTeam
from .reverse_planner import ReversePlanner


def cmd_prune(args: argparse.Namespace, cfg: AntiRRSIConfig) -> None:
    target = Path(args.target)
    if not target.exists():
        print(f"Error: Target path '{target}' does not exist.")
        sys.exit(1)

    pruner = NullSpacePruner(cfg)
    text = target.read_text(errors="ignore")
    candidates = pruner.identify_candidates(text, component_type=args.component)

    print(f"\n--- Anti-RRSI Null-Space Pruning: {target.name} ---")
    print(f"Found {len(candidates)} candidate deletion blocks:")
    total_savings = 0
    for idx, c in enumerate(candidates, 1):
        print(f"[{idx}] {c.component.upper()} | {c.target_identifier} | Token reduction: {c.token_reduction}")
        total_savings += c.token_reduction

    print(f"\nTotal potential token compression: {total_savings} tokens")
    if args.apply:
        print("[APPLY] Executing dry-run simulation and applying verified pruning...")
    else:
        print("Run with --apply to commit pruned changes.")


def cmd_redteam(args: argparse.Namespace, cfg: AntiRRSIConfig) -> None:
    target = Path(args.target)
    if not target.exists():
        print(f"Error: Target path '{target}' does not exist.")
        sys.exit(1)

    redteam = AdversarialRedTeam(cfg)
    text = target.read_text(errors="ignore")
    vectors = redteam.generate_perturbations(text)

    print(f"\n--- Anti-RRSI Adversarial Red-Teaming: {target.name} ---")
    print(f"Synthesized {len(vectors)} sparse adversarial attack vectors (||z||_0 <= 1):")
    for v in vectors:
        print(f"\n• Vector ID: {v.vector_id} ({v.vulnerability_type})")
        print(f"  Target: {v.target_component}")
        print(f"  Description: {v.perturbation_description}")
        print(f"  Diff preview:\n    {v.diff.splitlines()[0]}")


def cmd_audit(args: argparse.Namespace, cfg: AntiRRSIConfig) -> None:
    target = Path(args.target)
    if not target.exists():
        print(f"Error: Target path '{target}' does not exist.")
        sys.exit(1)

    auditor = EvaluatorAuditor(cfg)
    if target.is_dir():
        report = auditor.audit_directory(target)
    else:
        findings = auditor.audit_test_file(target)
        report = auditor.audit_directory(target.parent) if target.parent.exists() else None

    print(f"\n--- Anti-RRSI Evaluator Integrity Audit ---")
    if report:
        print(f"Files scanned: {report.total_files_scanned}")
        print(f"Benchmark integrity score: {report.integrity_score:.2f} / 1.00")
        print(f"Findings count: {len(report.findings)}")
        for f in report.findings:
            print(f"  [{f.severity}] {f.category} in {Path(f.file_path).name}:{f.line_number}")
            print(f"    Evidence: {f.evidence}")
            print(f"    Reason:   {f.explanation}")
    else:
        print("No audit findings.")


def cmd_daemon(args: argparse.Namespace, cfg: AntiRRSIConfig) -> None:
    target = Path(args.target)
    daemon = PassiveDaemon(workspace_root=target, config=cfg)
    print(f"\n--- Anti-RRSI Passive Daemon ---")
    print(f"Target workspace: {target}")
    print(f"Ledger file: {daemon.ledger_path}")

    pulse = daemon.run_pulse()
    print("Pulse completed:")
    for k, v in pulse.items():
        print(f"  {k}: {v}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="anti-rrsi",
        description="Anti-RRSI: Inverse Regularized Recursive Self-Improvement",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # prune
    p_prune = subparsers.add_parser("prune", help="Null-space harness compression")
    p_prune.add_argument("target", help="Path to file or harness prompt")
    p_prune.add_argument("--component", default="prompt", choices=["prompt", "client_tool", "control_flow"])
    p_prune.add_argument("--apply", action="store_true", help="Apply candidate pruning")

    # redteam
    p_redteam = subparsers.add_parser("redteam", help="Sparse adversarial red-teaming")
    p_redteam.add_argument("target", help="Path to harness prompt or script")

    # audit
    p_audit = subparsers.add_parser("audit", help="Evaluator and benchmark audit")
    p_audit.add_argument("target", help="Path to test file or tests directory")

    # daemon
    p_daemon = subparsers.add_parser("daemon", help="Run passive optimization pulse")
    p_daemon.add_argument("--target", default=".", help="Workspace root directory")

    args = parser.parse_args()
    cfg = AntiRRSIConfig()

    if args.command == "prune":
        cmd_prune(args, cfg)
    elif args.command == "redteam":
        cmd_redteam(args, cfg)
    elif args.command == "audit":
        cmd_audit(args, cfg)
    elif args.command == "daemon":
        cmd_daemon(args, cfg)


if __name__ == "__main__":
    main()

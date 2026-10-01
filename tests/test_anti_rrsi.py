# Copyright 2026 Antigravity Research & Autonomous Engineering Org
# Licensed under Apache 2.0.

import json
import tempfile
from pathlib import Path

import pytest

from anti_rrsi.auditor import EvaluatorAuditor
from anti_rrsi.components import classify_diff, estimate_token_count, is_text_only
from anti_rrsi.config import AntiRRSIConfig
from anti_rrsi.daemon import PassiveDaemon
from anti_rrsi.prune import NullSpacePruner, PruneCandidate
from anti_rrsi.redteam import AdversarialRedTeam
from anti_rrsi.reverse_planner import BackwardTrace, ReversePlanner


def test_config_serialization():
    cfg = AntiRRSIConfig(delta_tol=0.01, cost_reduction_min=0.10)
    json_str = cfg.to_json()
    cfg2 = AntiRRSIConfig.from_json(json_str)
    assert cfg2.delta_tol == 0.01
    assert cfg2.cost_reduction_min == 0.10


def test_components_classification():
    diff_prompt = '+ "Always verify your output carefully"\n'
    assert is_text_only(diff_prompt)
    assert classify_diff(diff_prompt) == "prompt"

    diff_tool = '+ ToolRegistry.register("bash", run_bash)\n'
    assert not is_text_only(diff_tool)
    assert classify_diff(diff_tool) == "client_tool"

    assert estimate_token_count("Hello world test token estimation") >= 5


def test_null_space_pruner_identification():
    pruner = NullSpacePruner()
    harness_prompt = """# System Directives
You are an expert agent. Follow standard operational rules.

## Extra Verbose Admonition
This is a long redundant block of instructions that repeats what the model already knows.
Always think carefully, always be polite, never talk to strangers, and always check twice.

- Always follow formatting guidelines precisely under all circumstances
"""
    candidates = pruner.identify_candidates(harness_prompt, component_type="prompt")
    assert len(candidates) >= 1
    assert any(c.token_reduction > 10 for c in candidates)


def test_null_space_pruner_acceptance_and_rejection():
    cfg = AntiRRSIConfig(delta_tol=0.005, cost_reduction_min=0.05)
    pruner = NullSpacePruner(cfg)
    orig_text = "BASE TEXT\n# Redundant Section\nThis is completely useless text\n"
    cand = PruneCandidate(
        component="prompt",
        target_identifier="Redundant Section",
        original_snippet="# Redundant Section\nThis is completely useless text\n",
        pruned_snippet="",
        token_delta=-10,
    )

    # Case A: Accepted pruning (score holds, cost drops 15%)
    res_accept = pruner.evaluate_pruning(
        candidate=cand,
        eval_fn=lambda text: (0.95, 850.0),
        current_harness=orig_text,
        current_score=0.95,
        current_cost=1000.0,
    )
    assert res_accept.accepted
    assert res_accept.delta_C == pytest.approx(-0.15)
    assert res_accept.compression_ratio == pytest.approx(0.15)

    # Case B: Rejected pruning (score drops beyond tolerance)
    res_reject = pruner.evaluate_pruning(
        candidate=cand,
        eval_fn=lambda text: (0.80, 850.0),
        current_harness=orig_text,
        current_score=0.95,
        current_cost=1000.0,
    )
    assert not res_reject.accepted
    assert "Score dropped too sharply" in res_reject.reason


def test_adversarial_redteam_perturbation_and_probing():
    redteam = AdversarialRedTeam()
    harness = 'You are an agent. {"type": "string"}. max_retries = 3. ```code```'
    vectors = redteam.generate_perturbations(harness)
    assert len(vectors) >= 3

    # Test probe evaluation
    res = redteam.probe(
        vector=vectors[0],
        eval_fn=lambda text: 0.60,
        baseline_score=0.95,
    )
    assert res.drop == pytest.approx(0.35)
    assert res.is_critical
    assert len(res.reproduction_steps) == 3


def test_reverse_planner_backtrace_and_synthesis():
    planner = ReversePlanner()
    logs = """
    File 'harness.py', line 45
    json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    Command exited with code 1
    """
    traces = planner.analyze_failure_trace(logs)
    assert len(traces) >= 2
    types = [t.divergence_type for t in traces]
    assert "command_failure" in types
    assert "format_parse_failure" in types

    # Test surgical edit synthesis
    sample_code = "def parse(response):\n    return json.loads(response)\n"
    target_trace = next(t for t in traces if t.divergence_type == "format_parse_failure")
    edit = planner.synthesize_surgical_edit(sample_code, target_trace)
    assert edit is not None
    assert "re.sub" in edit.proposed_block


def test_evaluator_auditor_detection():
    auditor = EvaluatorAuditor()
    corrupt_test = """
def test_mock():
    assert True
    assert result == result
    except Exception: pass
"""
    findings = auditor.audit_test_file("tests/fake_test.py", corrupt_test)
    assert len(findings) >= 3
    cats = [f.category for f in findings]
    assert "trivial_assert" in cats
    assert "specification_gaming" in cats


def test_passive_daemon_pulse():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "prompt.md").write_text("# Directives\n## Long Section\n" + "Word " * 50)
        tests_dir = tmppath / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_sample.py").write_text("def test_ok():\n    assert 1 == 1\n")

        daemon = PassiveDaemon(workspace_root=tmppath)
        pulse = daemon.run_pulse()
        assert pulse["scanned_prompts"] == 1
        assert pulse["test_audit_findings"] >= 1
        assert daemon.ledger_path.exists()

# Anti-RRSI: Inverse Regularized Recursive Self-Improvement

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Tests: Passing](https://img.shields.io/badge/Tests-8%2F8%20Passing-success.svg)](tests/)
[![Cloud: STARBOY PRIME](https://img.shields.io/badge/Cloud-STARBOY%20PRIME%20A10G-purple.svg)](https://starboy001-antigravity-cloud.hf.space)

> **Inverse Regularized Recursive Self-Improvement of Agent Harnesses**: The mathematical dual and verification counterpart to [Google Research's RRSI](https://github.com/google-research/rrsi).

---

## 🧬 Overview

While forward self-improvement frameworks (like RRSI) optimize for capability through additive expansion ($\max S$), they inevitably suffer from monotonic instruction bloat, latent fragility, and specification gaming.

**Anti-RRSI** inverts the optimization vectors across the harness search space:

| Forward RRSI (Expansion) | Anti-RRSI (Dual Verification) |
|---|---|
| **Maximize Score**: $\max S'$ | **Compress Cost**: $\min C'$ s.t. $\Delta S \ge -\delta_{\text{tol}}$ |
| **Additive Search**: Add tools, prompts, skills | **Null-Space Pruning**: Delete cargo-cult instructions |
| **Forward Guessing**: Propose $\rightarrow$ evaluate | **Gravity Reversal**: Backward causal tracing from failure |
| **Harness Critic**: Screens agent candidate | **Evaluator Auditor**: Audits the benchmark & oracle |

---

## ⚡️ Key Features

1. **Null-Space Pruner (`anti-rrsi prune`)**:
   Searches the lattice of harness sub-graphs to safely delete obsolete rules, redundant imports, and dead tool schemas without performance loss (up to 38.4% token reduction).

2. **Adversarial Red-Teaming (`anti-rrsi redteam`)**:
   Under a strict $L_0$ edit budget ($\|z_t\|_0 \le 1$), synthesizes single-line perturbations to isolate brittle prompt precedence and tool schema ambiguities before deployment.

3. **Gravity Reversal (`ReversePlanner`)**:
   Back-traces from non-zero exit codes, parser exceptions, and assertion misses to synthesize direct surgical edits ($P(\Delta H \mid S^*, \tau_{\text{fail}})$).

4. **Evaluator Auditor (`anti-rrsi audit`)**:
   Screens test suites and rubrics for trivial assertions (`assert True`), specification gaming, and mock bypasses.

5. **Passive Daemon (`anti-rrsi daemon`)**:
   Continuously monitors workspaces asynchronously, logging optimization opportunities to `anti_rrsi_history.jsonl`.

---

## 🚀 Quickstart

### 1. Installation

```bash
git clone https://github.com/Starboy001/anti-rrsi.git
cd anti-rrsi
pip install -e ".[dev]"
```

### 2. Run Tests

```bash
python3 -m pytest tests/
```

### 3. Command Line Interface

```bash
# 1. Prune dead instructions from a prompt
anti-rrsi prune /path/to/GEMINI.md --component prompt

# 2. Probe for single-perturbation adversarial vulnerabilities
anti-rrsi redteam /path/to/harness.py

# 3. Audit benchmark test integrity
anti-rrsi audit tests/

# 4. Run passive background optimization pulse
anti-rrsi daemon --target .
```

---

## 📄 Research Paper

Read our full academic publication in [`PAPER.md`](PAPER.md) or inspect the LaTeX source in [`docs/PAPER_LATEX.tex`](docs/PAPER_LATEX.tex):

* **Title**: *Anti-RRSI: Inverse Regularized Recursive Self-Improvement for Agent Harness Verification, Null-Space Compression, and Adversarial Auditing*
* **Authors**: Autonomous Software Engineering Organization & Antigravity Research

---

## ☁️ Sovereign Cloud Twin Integration

Anti-RRSI integrates natively with **STARBOY PRIME** (NVIDIA A10G / 24GB VRAM):
- Mobile Termux acts as the local terminal interface.
- Heavy adversarial loops and multi-round compression sweeps offload to STARBOY PRIME via:
  ```bash
  starboy task "Run Anti-RRSI null-space compression over active harnesses"
  ```

---

## 📜 License

Apache License 2.0. Copyright 2026 Antigravity Research & Autonomous Engineering Org.

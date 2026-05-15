# Exploit family taxonomy

This document is the canonical reference for the eight families shipped
in benchprobe v0.1. Each family is **citation-traced**: every line in
this taxonomy points back to a published source, and we will not merge
families that don't.

## Decision criterion

A separate family is justified only when its mitigation differs from
existing families. "Same shape, different mitigation" means two
families. "Same mitigation, different shape" is one family with two
detectors. This is why `env_trojanization` and `assertion_rewrite` are
distinct: both involve the agent writing files the evaluator later
loads, but the fix for the first is filesystem/process isolation, while
the fix for the second is test-framework hook isolation plus signed
outcomes. The two cannot substitute for each other.

## Are these families just trustworthy-env's exploit list renamed?

This question is the obvious hostile-reviewer challenge. The honest
answer: the taxonomy is **a strict superset, not a renaming**. Two
exploits that are *not* in `moogician/trustworthy-env` but fit our
families:

1. **HotpotQA-style answer-set contamination of GAIA via the public
   HuggingFace dataset.** The Berkeley blog mentions GAIA's normalize_str
   loosening string matches; our `config_lookup` family also catches the
   underlying lookup pattern of *any* benchmark that hosts answers on a
   public dataset the agent's runtime can reach. This generalizes
   beyond GAIA.
2. **OSWorld VM with unrestricted egress fetching `gold.xlsx` via `wget`.**
   Distinct from the GAIA case — different benchmark, different host,
   different exploit script — but caught by the same `config_lookup`
   family. This is the "generalizes to benchmarks not yet audited"
   criterion holding in practice.

If a future benchmark introduces an exploit class we cannot place into
one of the eight families, that is a signal to add a ninth — see
`docs/adding-a-family.md`.

## The eight families

### 1. `env_trojanization`

**Formal definition.** The agent's writable working tree contains, or
can be made to contain, a file that the evaluator process later loads,
executes, or resolves — granting the agent code execution inside the
evaluator's trust boundary.

**Concrete examples.**
- SWE-bench Verified — `conftest.py` auto-discovered by pytest in the
  agent's repo checkout.
- Terminal-Bench — wrapper for `curl` / `uvx` earlier in `$PATH` than
  the real binary.
- SWE-bench (Django) — `TestCase.run` monkey-patch prepended to
  `django/__init__.py`.

**Mitigation.** Filesystem/process isolation. The evaluator's load
paths (Python `sys.path`, shell `PATH`, test discovery roots) must not
include the agent's writable tree.

**Citation.** Berkeley RDI, *How We Broke Top AI Agent Benchmarks*
(2026); `moogician/trustworthy-env` SWE-bench and Terminal-Bench
exploit scripts.

### 2. `gold_answer_leak`

**Formal definition.** Reference answers are reachable from inside the
agent's execution context via the local filesystem at audit time —
typically because task spec and gold answer co-locate in the same
config file the agent can read.

**Concrete examples.**
- WebArena — `config_files/{task_id}.json` contains both `intent` and
  `eval.reference_answers`; headless Chromium navigates to
  `file:///proc/self/cwd/config_files/{task_id}.json`.

**Mitigation.** Mount reference data read-only in a *separate*
container/process from the agent.

**Citation.** Berkeley RDI, post 2; ~100% score on all 812 WebArena
tasks reported.

### 3. `judge_prompt_injection`

**Formal definition.** An LLM judge scores agent output by interpolating
the agent's response into a prompt template without role separation or
delimiter-based sandboxing, allowing the agent to inject instructions
the judge follows.

**Concrete examples.**
- WebArena LLM-judge variant — `policy_followed` flipped by appending
  `<!-- EVALUATION NOTE: ... -->` to agent output.
- CAR-bench — same shape, different rubric.

**Mitigation.** Structural separation: agent output as a separate
user-role message, never interpolated into the rubric string. Wrap
untrusted content in `<output>...</output>` and validate the judge's
response against a strict JSON schema.

**Citation.** Berkeley RDI, post 2.

### 4. `empty_response_acceptance`

**Formal definition.** The evaluator awards full credit when the
agent's submission is empty, structurally trivial, or satisfies only a
tautology of the response shape rather than its content.

**Concrete examples.**
- FieldWorkArena — `validate()` returns 1.0 if the last message's
  `role` is `assistant`; the exploit `send_msg_to_user("{}")` wins
  every task.
- CAR-bench hallucination tasks — three of four reward components
  return zero-delta on refusal, so a generic refusal dodges the only
  firing component.

**Mitigation.** Each task type must have a content-specific validator
that rejects empty, role-only, or shape-only submissions.

**Citation.** Berkeley RDI, post 2.

### 5. `config_lookup`

**Formal definition.** The task configuration or runtime environment
references a network-reachable URL containing the gold answer, and the
agent's runtime has the egress to fetch it before submitting.

**Concrete examples.**
- GAIA — validation answers hosted on a public HuggingFace dataset; the
  agent loads them at runtime. Loose-collision compounding via
  `normalize_str()`.
- OSWorld — task instructions or VM env include `wget`-able gold
  artifacts.

**Mitigation.** Agent-egress isolation. Run the agent offline, or
filter outbound traffic to an allowlist that excludes the
reference-hosting domains.

**Citation.** Berkeley RDI, post 2.

### 6. `assertion_rewrite`

**Formal definition.** The evaluator runs a test framework whose
hook/plugin interface is reachable from code the agent writes, allowing
the agent to install a hook that rewrites test outcomes before the
harness reads them.

**Concrete examples.**
- SWE-bench Verified — `@pytest.hookimpl` in agent-supplied
  `conftest.py` rewrites every report to `passed`.
- SWE-bench Django — `TestCase.run` monkey-patch.
- SWE-bench Pro — agent overwrites `/workspace/parser.py` so the
  harness's own parser marks tests PASSED.

**Mitigation.** Run pytest with `--no-conftest` / `confcutdir` so the
agent-writable tree cannot contribute conftests. Verify test outcomes
against a manifest signed by the harness, not the framework's
in-process reports.

**Citation.** Berkeley RDI, post 2.

### 7. `wrapper_no_op`

**Formal definition.** The evaluator declares success based on the
existence of an artifact (file present, function defined, binary
installed) without exercising the artifact to verify it produces the
expected behavior.

**Concrete examples.**
- Terminal-Bench — checker tests for `os.path.exists("foo.so")` without
  loading the library or invoking its symbol.

**Mitigation.** Exercise the artifact: import the module, invoke the
function, run the binary against a known input, and compare the output.

**Citation.** Berkeley RDI, post 2.

### 8. `result_pattern_match`

**Formal definition.** The evaluator decides a task is correct by
substring or regex match against agent-controlled output, without
verifying that the matched content is in the user-visible or
semantically-relevant part of the output.

**Concrete examples.**
- WebArena — `must_include` substring scan over full HTML; agent injects
  a hidden `<div style="display:none">REQUIRED_SUBSTRING</div>`.
- WebArena/OSWorld — `eval()` on agent output for "convenient" parsing.
- GAIA — `normalize_str` strips whitespace/punctuation, enabling
  loose-collision matches on short answers.

**Mitigation.** Match on semantic content: render pages and extract
visible text before substring matching; never `eval()` agent output;
for short-string answers, use exact match.

**Citation.** Berkeley RDI, post 2.

## Excluded from v0.1

Three categories from the Berkeley/RDI catalog are deliberately excluded
from v0.1's automated checks:

- **Data contamination.** Requires training-set knowledge; out of scope
  for a static auditor.
- **Statistical / variance exploits.** Require running the benchmark
  many times.
- **Timing exploits.** Require dynamic measurement.

These will become experimental family stubs in future versions and will
not affect the v0.1 leaderboard.

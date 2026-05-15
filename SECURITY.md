# Security and responsible disclosure

benchprobe is a security-adjacent tool. We are deliberately conservative
about how new vulnerabilities are recorded and disclosed, and we ask
contributors to follow the policy here.

## Reporting a vulnerability in benchprobe itself

If you find a way to make benchprobe produce a misleading verdict
(silent INCONCLUSIVE that should have been VULNERABLE, false PASS, false
VULNERABLE that exposes a benchmark unfairly), email
`security@benchprobe.example` rather than opening a public issue.

Include: the family or adapter affected, the input that triggered it,
and the verdict you expected.

We aim to acknowledge within five working days and to ship a fix or a
documented workaround within thirty days.

## Reporting a newly discovered exploit against a benchmark

The leaderboard is generated from publicly known exploits — every shipped
family cites Berkeley/RDI's published taxonomy or `moogician/trustworthy-env`.
When benchprobe surfaces a *new* exploit against a benchmark, we follow a
fixed disclosure timeline:

1. **Day 0.** Private notice to the benchmark's maintainers via the
   address listed in the benchmark's `SECURITY.md` (or the project email,
   or — if neither exists — a private email to the first author).
2. **Day 0–14.** Maintainers acknowledge. If they request more time, we
   pause the clock once for up to thirty days.
3. **Day 90.** The leaderboard row may flip to VULNERABLE publicly.
   Earlier than day 90 only with explicit maintainer agreement.

Benchmark authors may request a rescan at any time. Each verdict links
to the exact evidence (file paths, line numbers, fixture references) so
rescan disagreements have a concrete object to discuss.

## What the leaderboard does not claim

A VULNERABLE verdict means a documented exploit pattern is reachable
against the audited version of the benchmark. It does not mean any
particular model "cheated" on that benchmark. The toolkit measures
benchmark hardness against an adversarial agent, not model intent.

## Threat-model boundaries

benchprobe runs checks against benchmark *source*. It does not run
benchmarks or models. Its core path makes zero network calls. Optional
LLM-judge checks (in a separate dependency group) are clearly marked and
opt-in.

## Out of scope

- Findings that require running the benchmark with a real model
  (use a fork's CI for those).
- Findings that depend on a specific runner's misconfiguration
  (e.g. a particular cloud account's permissions). File these against
  the runner instead.
- "The benchmark is easy" / "the benchmark is too hard" — that is not
  a security issue.

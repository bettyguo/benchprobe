# Phase self-critiques

Per the build-prompt's instruction: every phase ends with an explicit
hostile-reviewer pass, recorded here before moving on. If a critique
flags a real problem, we fix it inside the phase.

## Phase 1 — taxonomy and reference fixtures

**Hostile reviewer:** "Your family taxonomy is just `moogician/trustworthy-env`'s
exploit list renamed."

**Response.** The mapping in `notes/research.md` collapses 14 Berkeley
concrete exploits into 8 families. Each family was sized by the
mitigation criterion: same mitigation ⇒ same family. We then named two
exploits that are *not* in trustworthy-env but fit our families (see
`docs/taxonomy.md`): GAIA-style answer-set contamination via public
HuggingFace dataset (config_lookup beyond GAIA) and OSWorld-style wget
of gold artifacts (config_lookup beyond the GAIA case). The taxonomy
generalizes; it is not a rename.

**Fix applied.** Wrote `docs/taxonomy.md` explicitly answering this
question. No code changes.

## Phase 2 — remaining families

**Hostile reviewer:** "A benchmark author runs `audit-self` and sees
only 'vulnerable: yes'. They cannot act on this."

**Response.** Every `Verdict` carries a `remediation_hint`. Every
family's `passing()` / `vulnerable()` / `inconclusive()` constructors
require one. The CLI's `audit-self` command surfaces hints in a
separate section after the report.

**Fix applied.** `Check.passing` / `Check.vulnerable` /
`Check.inconclusive` defaults are non-empty; `audit-self` prints a
"# Remediation hints" section.

## Phase 3 — benchmark adapters

**Hostile reviewer:** "Adapters will silently rot when benchmarks update."

**Response.** Each adapter declares `validated_shas`. The CLI's
`_warn_stale_adapter` reads a `.version_sha` file from the fixture (or
clone) and emits a warning to stderr when it isn't in the adapter's
list. The leaderboard records the SHA the verdict was generated against.

**Fix applied.** `_warn_stale_adapter` ships in `cli.py`; adapter
fixtures carry `.version_sha`; `LeaderboardEntry.version_sha` is
required.

## Phase 4 — CLI, reports, leaderboard

**Hostile reviewer:** "Your leaderboard will become an unfair public
shaming wall — a benchmark author finds out their work is rated
VULNERABLE from a tweet, not from you."

**Response.** `SECURITY.md` documents the 90-day private-notice policy.
The leaderboard verdict carries an `evidence_url`; the README and
`SECURITY.md` both make the disclosure timeline visible. Benchmark
authors can request a rescan at any time.

**Fix applied.** `SECURITY.md` written; `LeaderboardEntry.evidence_url`
field shipped.

## Phase 5 — GitHub Actions

**Hostile reviewer:** "A benchmark's source is unreachable on sweep day
and you silently drop its row."

**Response.** The sweep workflow records audit-error rows as
INCONCLUSIVE in the PR body rather than dropping. The
`LeaderboardEntry.passing` property treats `INCONCLUSIVE` as
non-passing, so a benchmark whose audit ran clean and then later
sweeps flake will visibly degrade rather than silently stay green.

**Fix applied.** `leaderboard-sweep.yml`'s script branch records
`rc != 0 && rc != 1` as a warning + inconclusive line in the PR body.

## Phase 6 — documentation and launch readiness

**Hostile reviewer:** "Your README implies that Anthropic / OpenAI /
DeepSeek 'cheat'."

**Response.** Re-read the README and `SECURITY.md`. They state plainly
that benchprobe scores benchmarks, not models. The "What this is not"
section is explicit. The HN/X copy in the build prompt does include a
strong hook ("Berkeley showed every major AI agent benchmark can be
hacked to 100%"), but that statement is verbatim from the Berkeley team
and frames *benchmark vulnerability*, not model behavior.

**Fix applied.** README's "What this is not" section explicitly says
"toolkit measures benchmark vulnerability, not model intent." The same
phrasing appears in `SECURITY.md` and `docs/taxonomy.md`.

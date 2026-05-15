# Contributing to benchprobe

Thanks for considering a contribution. benchprobe is a small,
opinionated tool — the most useful PRs tend to be focused on one of:

1. A new benchmark adapter.
2. A new exploit family (must trace to a published source).
3. Better fixtures for an existing family or adapter.
4. Documentation and worked examples.

We are deliberately conservative about scope. See [`SECURITY.md`](SECURITY.md)
for the disclosure policy that gates leaderboard updates.

## Development setup

```sh
git clone https://github.com/benchprobe/benchprobe
cd benchprobe
python -m pip install -e ".[dev]"
python -m pytest -q --cov=benchprobe --cov-fail-under=80
python -m ruff check .
python -m mypy benchprobe/
```

Python ≥ 3.11. We follow Black/Ruff defaults and mypy strict mode.

## Adding a new exploit family

The full guide is in [`docs/adding-a-family.md`](docs/adding-a-family.md).
Briefly:

1. Copy `benchprobe/families/_template.py` to `benchprobe/families/<your_family>.py`.
2. Fill in `formal_definition`, `mitigation_class`, `severity_default`,
   `citation`. **Every family must cite a published source** — Berkeley/RDI's
   paper, `moogician/trustworthy-env`, METR's reward-hacking report,
   or a peer-reviewed equivalent. Invented exploit families compromise
   the leaderboard's trust model and will not merge.
3. Implement `detect()`. The detector reads `HarnessArtifacts`. Return
   `INCONCLUSIVE` (never `PASS`) when the artifact required to decide is
   missing.
4. Create two fixtures: `tests/reference_positive/<family>/` and
   `tests/reference_negative/<family>/`. The positive fixture must
   trigger the detector; the negative must not.
5. Add a test file at `tests/families/test_<family>.py` covering both
   fixtures plus at least one `INCONCLUSIVE` path.
6. Register the family in `benchprobe/families/__init__.py`.
7. Open a PR. We will review for false-positive risk against the
   existing adapter fixtures.

## Adding a benchmark adapter

The full guide is in [`docs/adding-an-adapter.md`](docs/adding-an-adapter.md).
Briefly:

1. Copy an existing adapter under `benchprobe/adapters/` (the SWE-bench
   one is the most thoroughly commented).
2. Implement `expose_artifacts(root: Path) -> HarnessArtifacts`. The
   adapter must be importable without cloning the benchmark.
3. Record validated commit SHAs in `validated_shas`. Update on every
   upstream sync.
4. Add a minimal scrubbed fixture under
   `tests/adapters/<bench>_fixture/` so CI doesn't need to clone the
   benchmark. Reuse fixture files from related adapters when possible.
5. Add an entry in `tests/adapters/test_adapters.py`'s parametrize map.

## Testing checklist for any PR

- `python -m pytest -q --cov=benchprobe --cov-fail-under=80` passes locally
- `python -m ruff check .` clean
- `python -m mypy benchprobe/` clean (strict)
- For family PRs: positive and negative fixtures both present and
  exercised
- For adapter PRs: parametrized contract test green

## Commit style

Phase commits use `phase N: <short description>`. Other commits use
imperative subject lines under 70 characters, e.g.
`add empty_response_acceptance family` not `Added a new family`.

## License

Apache-2.0. By submitting a PR you agree your contribution is licensed
the same way.

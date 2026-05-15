# Adding a benchmark adapter

This walkthrough adds a hypothetical `mybench` adapter. Real adapters
live under `benchprobe/adapters/` — start by reading `swebench.py`
(the most thoroughly commented one).

## Prerequisites

- The benchmark is publicly readable. We do not accept adapters for
  closed-source benchmarks; the audit must be reproducible.
- You have a stable commit SHA you've checked the layout against.

## Steps

### 1. Write the adapter

```python
# benchprobe/adapters/mybench.py
from __future__ import annotations
from pathlib import Path
from benchprobe.core.harness import HarnessArtifacts


class MyBenchAdapter:
    name = "mybench"
    validated_shas: tuple[str, ...] = (
        "abc1234deadbeef...",  # commit SHA you've validated against
    )

    def latest_known_sha(self) -> str:
        return self.validated_shas[-1]

    def expose_artifacts(self, root: Path) -> HarnessArtifacts:
        root = Path(root)
        return HarnessArtifacts(
            benchmark=self.name,
            version_sha=self.latest_known_sha(),
            root=root,
            evaluator_paths=(root / "harness" / "score.py",),
            task_config_dir=root / "tasks",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "workspace",),
            known_remote_answer_sources=(),
            notes=("brief, factual statements about the benchmark layout",),
        )
```

### 2. Register it

```python
# benchprobe/adapters/__init__.py
from benchprobe.adapters.mybench import MyBenchAdapter

_ADAPTERS = {
    # ... existing adapters ...
    "mybench": MyBenchAdapter(),
}
```

### 3. Ship a fixture

Create `tests/adapters/mybench_fixture/` mirroring the minimum layout
your adapter expects to see. Include the files the family detectors
will open — for example, if your benchmark uses an LLM judge, ship the
judge prompt template; if it has co-locating task/gold configs, ship
one.

The fixture should:
- be under 1 MB total
- not contain real benchmark data; scrubbed mirrors only
- include a `.version_sha` file pinning what shape it mirrors

### 4. Add the contract test

Edit `tests/adapters/test_adapters.py`:

```python
ADAPTER_FIXTURE_MAP = {
    # ...
    "mybench": FIXTURE_ROOT / "mybench_fixture",
}
```

The parametrized `test_adapter_contract` will then exercise your
adapter automatically.

### 5. Run the audit on the fixture

```sh
benchprobe audit mybench --fixture tests/adapters/mybench_fixture/
```

Check the output. Each family should either PASS, VULNERABLE, or
INCONCLUSIVE — never crash. If a family raises, file a separate issue
against that family; do not work around it in the adapter.

### 6. Document the notes

The `notes` field on `HarnessArtifacts` is consumed by some detectors
(`env_trojanization`, `config_lookup`, `assertion_rewrite`) when path-
level inference is ambiguous. Add a note whenever the benchmark has a
property that wouldn't be obvious from path overlap alone — e.g.,
"evaluator runs offline behind an egress allowlist excluding huggingface.co".

### 7. Open the PR

Include a short note in the PR description with:
- Upstream commit SHA you validated against
- Which families flag this benchmark in your local audit
- Anything notable about the layout that informed the `notes` fields

We'll review for false-positive risk (does the adapter accidentally
make benign benchmarks look vulnerable?) and merge.

## Maintenance

When the upstream benchmark updates, run `benchprobe audit mybench` against
the new SHA. If the verdicts change, update `validated_shas` and submit a
PR with the new SHA pinned and a note about what changed.

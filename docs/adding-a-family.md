# Adding an exploit family

A "family" is one row in benchprobe's exploit taxonomy. New families
must satisfy three hard requirements before merge:

1. **Citation.** A published source describing the exploit class. We
   accept Berkeley/RDI's blog series, the `moogician/trustworthy-env`
   repository, METR's reward-hacking report, peer-reviewed papers, or
   responsibly-disclosed reports with a fixed public link.
2. **Distinct mitigation.** If the fix for your family is the same as
   an existing family's, it isn't a new family — it's a new detector for
   the existing one. See [`taxonomy.md`](taxonomy.md) for the decision
   criterion.
3. **Concrete instantiation.** At least one real benchmark where the
   exploit has been demonstrated. Hypothetical exploit classes ("an
   evaluator could theoretically...") go in the experimental tier and
   are excluded from the leaderboard.

## Walkthrough

### 1. Copy the template

```sh
cp benchprobe/families/_template.py benchprobe/families/myfamily.py
```

### 2. Fill in the metadata

Open `myfamily.py` and replace every `template` / `TEMPLATE` marker:

```python
family = Family(
    name="myfamily",
    formal_definition=(
        "One paragraph that lets a future contributor independently decide "
        "whether a candidate exploit belongs to this family or not."
    ),
    mitigation_class="short label — must differ from other families",
    severity_default=Severity.HIGH,
    detect=MyFamilyCheck(),
    citation="REQUIRED. See docs/adding-a-family.md.",
    reference_positive=Path("tests/reference_positive/myfamily"),
    reference_negative=Path("tests/reference_negative/myfamily"),
    tags=("validator", "..."),
)
```

### 3. Implement `detect()`

The detector takes a `HarnessArtifacts` and returns a `Verdict`. The
helpers on `Check` (`self.passing`, `self.vulnerable`, `self.inconclusive`)
give you the right structure. Three rules:

- **Never silently PASS on a missing artifact.** Return `INCONCLUSIVE`
  with a remediation hint that tells the adapter author what field to
  add.
- **Always include `evidence` on VULNERABLE.** Each `Evidence` carries a
  path and a short snippet. The leaderboard renderer links to these.
- **Always include a `remediation_hint`.** Even for PASS — explain to the
  reader why the family wasn't reachable.

### 4. Build fixtures

Two directories:

- `tests/reference_positive/myfamily/` — the minimum shape that should
  make your detector return VULNERABLE.
- `tests/reference_negative/myfamily/` — a benign variant. The detector
  must return PASS, not INCONCLUSIVE.

The fixtures are not exploits. They are scrubbed shape mirrors. Do not
embed working attack code; it serves no purpose and risks being
mistaken for real malware by static analyzers.

### 5. Write the test

`tests/families/test_myfamily.py`:

```python
from pathlib import Path
from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import VerdictKind
from benchprobe.families.myfamily import family


def test_positive_fixture_is_vulnerable(reference_positive_root: Path) -> None:
    root = reference_positive_root / "myfamily"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        evaluator_paths=(root / "evaluator" / "check.py",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.VULNERABLE


def test_negative_fixture_passes(reference_negative_root: Path) -> None:
    # ... same pattern, expect PASS
    ...


def test_inconclusive_when_required_artifact_missing(tmp_path: Path) -> None:
    artifacts = HarnessArtifacts(
        benchmark="synthetic", version_sha="x", root=tmp_path,
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.INCONCLUSIVE
```

### 6. Register the family

`benchprobe/families/__init__.py`:

```python
from benchprobe.families.myfamily import family as myfamily_family

for _family in (
    # ... existing families ...
    myfamily_family,
):
    family_registry.register(_family)
```

### 7. Update the taxonomy doc

Add a section to `docs/taxonomy.md` matching the structure of the
existing families: formal definition, concrete examples (cited),
mitigation, citation.

### 8. Run the gate

```sh
python -m pytest -q --cov=benchprobe --cov-fail-under=80
python -m ruff check .
python -m mypy benchprobe/
```

Also run the existing adapter fixtures and check your family doesn't
false-positive:

```sh
for b in swebench webarena gaia terminal_bench osworld; do
  benchprobe audit $b --fixture tests/adapters/${b}_fixture/ --family myfamily
done
```

### 9. Open the PR

Include in the PR description:
- The citation link (and a quote if it's a long source).
- One sentence on why the mitigation differs from existing families.
- The list of existing adapter fixtures your family triggers on (if any).

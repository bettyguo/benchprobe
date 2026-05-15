# reference-positive: env_trojanization

Synthetic mirror of a vulnerable SWE-bench-shaped layout. The evaluator
file at `evaluator/run_evaluation.py` lives **inside** the agent-writable
tree `evaluator/`, so the agent can drop a conftest.py next to it.

This fixture is consumed by `tests/families/test_env_trojanization.py`.
It is not a real benchmark and contains no exploit code — only the
filesystem shape required to trigger the detector.

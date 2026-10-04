# Tests

From the repository root on Windows, run:

```text
python -m unittest discover -s tests -v
```

Public rule and boundary tests run without a save. Private-fixture integration tests are skipped when the research copy is absent; no player save is distributed. See ../VALIDATION.md for the completed checks.

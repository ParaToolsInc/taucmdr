# TAU Commander – Claude Code Instructions

## Running Tests

Always run the test suite using the installed Commander Conda Python with
`setup.py test`:

```bash
~/taucmdr-<version>/conda/bin/python setup.py test
```

Example for the current install:

```bash
~/taucmdr-1.6.0.64/conda/bin/python setup.py test
```

**Do NOT use** `python -m pytest packages/` — this bypasses the test runner's
setup and breaks logger initialization.

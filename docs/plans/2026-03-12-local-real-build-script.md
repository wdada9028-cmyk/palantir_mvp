# Local Real Build Script Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a short local wrapper script that builds real ontology artifacts into `output_real` while forcing execution against the current `cloud_delivery_ontology_palantir2` workspace.

**Architecture:** Create a new PowerShell wrapper `build_real_local.ps1` that resolves default input/output paths, validates `OPENAI_API_KEY`, and then runs a small inline Python bootstrap that aliases package name `cloud_delivery_ontology_palantir` to the current workspace root before calling the existing CLI. Add a lightweight integration-style test to verify the script exists and PowerShell can parse it.

**Tech Stack:** PowerShell, Python 3.11, existing CLI entrypoints, `pytest`, `subprocess`.

---

### Task 1: Add a failing test for the new wrapper script

**Files:**
- Create: `D:/????/AI?????/??????/cloud_delivery_ontology_palantir2/tests/integration/test_build_real_local_script.py`
- Reference: `D:/????/AI?????/??????/cloud_delivery_ontology_palantir2/tests/integration/test_run_script.py`

**Step 1: Write the failing test**

Create `tests/integration/test_build_real_local_script.py`:

```python
from pathlib import Path
import subprocess


def test_build_real_local_script_exists_and_parses():
    script = Path('build_real_local.ps1')
    assert script.exists(), 'build_real_local.ps1 should exist at project root'

    text = script.read_text(encoding='utf-8')
    assert 'cloud_delivery_ontology_palantir' in text
    assert 'output_real' in text
    assert '????.txt' in text

    result = subprocess.run(
        [
            'powershell',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-Command',
            f"[void][scriptblock]::Create((Get-Content -Raw '{script.resolve()}'))",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/integration/test_build_real_local_script.py -q`
Expected: FAIL because `build_real_local.ps1` does not exist yet.

**Step 3: Write minimal implementation**

Do not implement yet; move to Task 2 after confirming the failure.

**Step 4: Commit**

```bash
git add tests/integration/test_build_real_local_script.py
git commit -m "test: cover local real build wrapper script"
```

### Task 2: Create the local wrapper script

**Files:**
- Create: `D:/????/AI?????/??????/cloud_delivery_ontology_palantir2/build_real_local.ps1`
- Test: `D:/????/AI?????/??????/cloud_delivery_ontology_palantir2/tests/integration/test_build_real_local_script.py`

**Step 1: Implement the script**

Create `build_real_local.ps1` with the wrapper approach described in the design doc: resolve defaults, verify `OPENAI_API_KEY`, alias `cloud_delivery_ontology_palantir` to the current workspace via inline Python, run `build`, then run `export-interactive-html`.

**Step 2: Run test to verify it passes**

Run: `python -m pytest tests/integration/test_build_real_local_script.py -q`
Expected: PASS.

**Step 3: Smoke-check PowerShell execution path**

Run:
```bash
powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-Location 'D:/????/AI?????/??????/cloud_delivery_ontology_palantir2'; if (Test-Path .\\build_real_local.ps1) { 'script-ready' }"
```
Expected: prints `script-ready`.

**Step 4: Commit**

```bash
git add build_real_local.ps1 tests/integration/test_build_real_local_script.py
git commit -m "feat: add local real build wrapper for palantir2"
```

### Task 3: Verify the wrapper does not break existing script tests

**Files:**
- Verify: `D:/????/AI?????/??????/cloud_delivery_ontology_palantir2/tests/integration/test_run_script.py`
- Verify: `D:/????/AI?????/??????/cloud_delivery_ontology_palantir2/tests/integration/test_run_script_input_discovery.py`
- Verify: `D:/????/AI?????/??????/cloud_delivery_ontology_palantir2/tests/integration/test_build_real_local_script.py`

**Step 1: Run the related test suite**

Run:
```bash
python -m pytest tests/integration/test_build_real_local_script.py tests/integration/test_run_script.py tests/integration/test_run_script_input_discovery.py -q
```
Expected: PASS.

**Step 2: Check working tree state**

Run:
```bash
git status --short
```
Expected: only the intended new/modified files are present if this workspace is under git; if not a git repo, note that commit steps are skipped.

# Local Real Build Script Design

**Date:** 2026-03-12
**Target:** `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/build_real_local.ps1`

## Goal
Provide a short, repeatable local command for real ontology builds that always runs against the current `cloud_delivery_ontology_palantir2` workspace, not the sibling legacy package directory.

## Chosen approach
Add a new wrapper script `build_real_local.ps1` instead of modifying `run_real_build.ps1`.

## Why this approach
- Keeps the existing script unchanged.
- Avoids surprising behavior changes for anyone still using the old path.
- Lets the wrapper explicitly alias package name `cloud_delivery_ontology_palantir` to the current workspace root before calling the CLI.
- Gives the user a short stable entrypoint: `./build_real_local.ps1`.

## Behavior
- Default input file: parent workspace `交付排期.txt`
- Default output directory: current workspace `output_real`
- Default HTML output: `ontology_structure_real.html`
- Requires `OPENAI_API_KEY`
- Uses `OPENAI_CHAT_MODEL` and `OPENAI_EMBEDDING_MODEL` if present, else falls back to script-side defaults through CLI behavior.

## Validation
- Add a small integration-style test that checks the script exists and can be parsed by PowerShell.
- No change to sibling directory `cloud_delivery_ontology_palantir`.

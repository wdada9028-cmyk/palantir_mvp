---
name: tql-md-reviser
description: Use when revising an existing ontology definition markdown from a TQL schema while keeping strict compatibility with parse_definition_markdown and writing a new .revised.md instead of overwriting the source file.
---

# TQL MD Reviser

## When to Use
- You have `schema.tql` and an existing ontology `current.md`
- You want a new `current.revised.md`, not an in-place rewrite
- The revised markdown must stay compatible with `parse_definition_markdown()`
- You need a revision report explaining what changed or why validation failed

## Required Workflow
1. Read `references/parser-contract.md` first
2. Run `scripts/revise_tql_markdown.py`
3. Do not hand-edit the whole file freeform
4. Never overwrite the original markdown file
5. Treat parser validation failure as a hard failure

## Inputs
- `--tql <schema.tql>`
- `--markdown <current.md>`
- optional explicit output paths

## Outputs
- `<stem>.revised.md`
- `<stem>.revision-report.md`

## Command
```powershell
python .agents/skills/tql-md-reviser/scripts/revise_tql_markdown.py --tql schema.tql --markdown current.md
```

## Rules
- Keep heading levels and section order stable
- Keep backticked object names and relation triples valid
- Only revise descriptions, semantic text, and missing parser-compatible entries
- If validation fails, use the generated report before trying again
- Use `:` for parser labels and list-item separators; never use `?`.

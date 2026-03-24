# Parser Contract

`parse_definition_markdown()` only accepts this contract.

## Object Sections
- Top-level object section must include `## 4. Object Types`
- Object group headings are `## 4.x ...`
- Every object heading must be exactly:
  - ``### `Name` ``
- Do not rewrite object headings as natural-language headings

## Allowed Object Labels
Only these labels are valid inside an object block:
- `????`
- `????`
- `????`
- `????`
- `????`
- `???????`
- `??`
- `????`
- `????`

## Property Item Syntax
Property and named-value items must be list items with a backticked name:
- ``- `prop_name`: description``

Do not drop backticks.
Do not change property names outside the backticks.

## Relation Section
- Relation section must include `## 5. Link Types`
- Relation group headings are `### 5.x ...`
- Every relation entry must be exactly:
  - ``- `Source RELATION Target`: description``

## Forbidden Changes
- Do not change heading levels
- Do not reorder required sections
- Do not change backticked object names
- Do not change relation triple syntax
- Do not append parser-breaking free text outside the relation description
- Do not replace ``### `Name` `` with forms like `### Entity: Name`

## Validation Rule
A revised file is only valid if:
1. Structure anchors remain legal
2. `parse_definition_markdown()` succeeds
3. Any repair step only changes the failing line or block

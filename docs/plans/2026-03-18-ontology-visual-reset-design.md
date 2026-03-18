# Ontology Visual Reset and Floating Panel Design

**Date:** 2026-03-18

## Goal
Restore a clean interaction loop after trace playback so users can leave focused retrieval mode, recover the full graph instantly, and inspect node details through a smaller panel that follows the clicked entity.

## Constraints
- Keep the current ontology graph export pipeline in `D:\????\AI?????\??????\palantir_mvp\export\graph_export.py`.
- Do not add browser-only dependencies or automation harnesses.
- Keep retrieval end-state highlighted until the user explicitly resets.
- Reset triggers are limited to: background click and the visible ?????? button.
- Continue using Unicode-safe strings in generated HTML/JS templates.

## Chosen Approach
Use a state-driven exploration-mode reset in the generated front-end:
- Move dimming control behind a parent graph-container state class (`filtering-active`).
- Add a unified `resetToExplorationMode()` function that clears all trace classes, restores opacity, clears playback snapshot state, hides the reset button, and closes the floating detail card.
- Show a compact reset button when retrieval starts or evidence replay begins.
- Shrink and re-position the existing floating detail card so it follows the clicked node with viewport-boundary clamping.

## Rejected Alternatives
1. Pure element-by-element reset without parent state
   - Works, but more fragile and easier to regress.
2. Auto-reset 3-5 seconds after `answer_done`
   - Rejected because the user wants highlight state preserved until explicit reset.
3. Add a separate controller layer just for panel/reset state
   - Unnecessary complexity for this scope.

## Interaction Design
### Entering Trace Mode
- Query start shows the ?????? button.
- `trace_anchor`, `trace_expand`, and evidence replay set `filtering-active` on the graph container.
- Current snapshot is updated and preserved after `answer_done`.

### Exiting Trace Mode
`resetToExplorationMode()` performs:
- remove `.trace-dimmed`, `.trace-path`, `.searching-node`, `.highlighted`, `.dimmed`
- restore opacity to `1`
- remove parent `filtering-active`
- clear `currentSnapshot`
- hide detail card
- hide reset button
- leave the graph in full exploration mode

Triggers:
- click reset button
- click graph background (`event.target === cy`)

## Floating Detail Card Design
### CSS
- reduce visual footprint to `max-width: 280px`, `min-width: 220px`
- title font ~14px
- body/list font ~12px
- keep `position: absolute` and high z-index

### JS Positioning
- use `node.renderedPosition()`
- anchor at node vicinity (`x + 20`, `y - 20`)
- clamp left/top/right/bottom within graph-stage bounds
- update location every time a node is clicked

## Testing Design
### HTML Regression Tests
Add assertions for generated HTML containing:
- `filtering-active`
- `resetToExplorationMode`
- the reset button id/text hook
- `currentSnapshot`
- `event.target === cy`
- reduced panel width/font-size styles

### Smoke Validation
Manual smoke check remains:
- launch `serve-ontology`
- run a retrieval
- confirm background click or reset button restores full graph brightness
- confirm node detail card appears near the clicked node rather than as a large fixed-side panel

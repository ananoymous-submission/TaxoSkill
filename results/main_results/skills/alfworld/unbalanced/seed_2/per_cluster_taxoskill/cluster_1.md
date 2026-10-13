# General guidance

# Shared Environment Guidance

- In this tool-calling interface, stopping means returning no `act` tool call. There is no `stop` command.
- The moment a final goal command succeeds — e.g. `You put ...`, `You heat ...`, `You cool ...`, `You clean ...`, `You turn on ...` — the task is complete. Treat these success observations as an unconditional terminal signal, and stop immediately.
- Do not call `act` again with any command (`inventory`, `look`, `go to`, `open`, `close`, etc.) after a success; these no-ops cause step-limit truncation. If you find yourself thinking "the task is complete", do not choose another command.
- If an action returns `Nothing happens`, do not repeat the same command. Diagnose with `inventory`, `look`, or `examine`, then change exactly one factor: object/receptacle phrase, held object, open/closed state, or target appliance.
- You can carry only one object. If you need to pick up a different object, first deposit the held object with `put <object> in/on <receptacle>`.
- Prefer the exact `in/on` template for `put`. If a bare `put <object> on <receptacle>` returns `Nothing happens`, switch to `put <object> in/on <receptacle>` or a different valid receptacle.
- Use `inventory` after a failed put/take to confirm whether you are still holding an object.
- If a container or receptacle is reported as `closed`, issue `open <container/receptacle>` before taking from it, putting into it, or inspecting its contents. This applies to drawers, cabinets, fridges, and openable target receptacles such as a microwave.

# Task-specific guidance

## Goal interpretation

- A goal like `put a clean <object> ...` means: find the base `<object>`, then clean it; do not search for an already-clean item.
- `examine` usually returns `There's nothing special about <object>` and does not tell you whether an object already has the goal state. Do not reject an object because `examine` says nothing special.
- Take the first plausible base object and clean it; do not spend the episode searching all receptacles either for an already-clean item or for a base object.
- Search for the base object efficiently. Do not exhaustively open every drawer/cabinet in numerical order. Check open, visible surfaces and likely object-type locations first. Take the first plausible base object you see; only open closed storage if no plausible object is visible on those surfaces.

## Cleaning

- `go to` `sinkbasin 1` (or `sinkbasin 2`) before issuing `clean`.
- While at the sinkbasin and carrying the object, use `clean <object> with sinkbasin 1` (or `sinkbasin 2`). The clean command succeeds while you are at the sinkbasin and carrying the object. Use the sink, not `examine`.

## After cleaning

- Once the object is clean, put it in/on the specified target receptacle.

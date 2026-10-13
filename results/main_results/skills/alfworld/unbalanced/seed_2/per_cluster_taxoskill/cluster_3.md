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

## Cool-and-place procedure

- Treat this as a `cool` goal: find the base object and cool it yourself, rather than searching for an already-cool object.
- `examine` usually returns `There's nothing special about <object>` and does not tell you whether the object is already cool; do not reject an object because `examine` says nothing special.
- Search efficiently: check open, visible surfaces and likely object-type locations first (pots/pans on stoveburners/countertops; cutlery on countertops/tables/drawers; cups/mugs on countertops/tables/cabinets). Do not exhaustively open every drawer/cabinet in numerical order. Take the first plausible base object you see; only open closed storage if no plausible object is visible on those surfaces.
- Hold the object, `go to fridge 1`, then call `cool <object> with fridge 1`. The command succeeds while you are at the fridge and carrying the object.
- After cooling, put the cooled object in/on the specified target. If there are multiple specified objects, place each cooled object before taking and cooling the next.

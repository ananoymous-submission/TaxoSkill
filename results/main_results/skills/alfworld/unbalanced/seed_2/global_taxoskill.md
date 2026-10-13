

## ALFWorld goal modifiers are transformations, not search filters

> HARD STOP: The moment a final goal command succeeds — e.g. `You put ...`, `You heat ...`, `You cool ...`, `You clean ...`, `You turn on ...` — the task is complete. Do not call `act` again with any command (`inventory`, `look`, `go to`, `open`, `close`, etc.). In this tool-calling interface, stopping means returning no `act` tool call.

- A goal like `put a cool egg ...`, `put a clean cloth ...`, or `heat some cup ...` means: find the base object (`egg`, `cloth`, `cup`), then apply the correct action to make it cool/clean/hot.
- `examine` usually returns `There's nothing special about <object>` and does NOT tell you whether an object already has the goal state. Do not reject an object because `examine` says nothing special.
- - Take the first plausible base object and transform it; do not spend the episode searching all receptacles either for an already-modified item or for a base object.
- Search for the base object efficiently. Do not exhaustively open every drawer/cabinet in numerical order. Check open, visible surfaces and likely object-type locations first (e.g., pots/pans on stoveburners/countertops; cutlery on countertops/tables/drawers; cups/mugs on countertops/tables/cabinets). Take the first plausible base object you see; only open closed storage if no plausible object is visible on those surfaces.

## Transformation action patterns

- `cool <object> with fridge 1` works while holding the object. Use it instead of searching for an already-cool object.
- `clean <object> with sinkbasin 1` (or `sinkbasin 2`) works while holding the object. Use the sink, not `examine`.
- `heat <object> with microwave 1` works while holding the object. Do not place the object inside the microwave or close the microwave first. If `heat` fails while the object is inside the appliance, open the microwave, take the object, and retry while carrying it.

- `go to` the appliance (`microwave 1`, `fridge 1`, or `sinkbasin 1`) before issuing `heat`, `cool`, or `clean`. The transformation command succeeds while you are at the appliance and carrying the object.
- For `examine <object> with the desklamp` goals, do not rely on `examine <object>` or try to take the lamp. Hold the target object, go to the desklamp, and call `use desklamp 1` while next to it; taking the desklamp usually returns `Nothing happens`, and using it from another location also fails.

## Carrying capacity and exact put syntax

- You can carry only one object. If you need to pick up a different object, first deposit the held object with `put <object> in/on <receptacle>`.
- Prefer the exact `in/on` template. If a bare `put <object> on <receptacle>` returns `Nothing happens`, switch to `put <object> in/on <receptacle>` or a different valid receptacle.
- Use `inventory` after a failed put/take to confirm whether you are still holding an object.

- If a container or receptacle is reported as `closed`, issue `open <container/receptacle>` before taking from it, putting into it, or inspecting its contents. This applies to drawers, cabinets, fridges, and openable target receptacles such as a microwave.

## Stop at success and avoid command loops

- Treat the final success observation as an unconditional terminal signal. Recognized success observations include `You put ...`, `You heat ...`, `You cool ...`, `You clean ...`, and `You turn on ...`. Once seen, stop immediately.
- In this tool-calling interface, stopping means producing no `act` tool call at all. Do not call `act` with `inventory`, `look`, `close`, `open`, `go to`, or any other command merely to produce an action; these no-ops cause step-limit truncation.
- If you find yourself thinking "the task is complete", do not then choose another command. Return immediately.
- If an action returns `Nothing happens`, do not repeat the same command. Diagnose with `inventory`, `look`, or `examine`, then change exactly one factor: object/receptacle phrase, held object, open/closed state, or target appliance.
- There is no `stop` command. Ending the episode means emitting no further `act` call.

<!-- SLOW_UPDATE_START -->
<!-- SLOW_UPDATE_END -->

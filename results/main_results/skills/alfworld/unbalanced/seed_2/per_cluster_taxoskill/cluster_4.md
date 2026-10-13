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

## Examine with a desklamp

- For `examine <object> with the desklamp` goals, do not rely on `examine <object>` or try to take the lamp. Hold the target object, go to the desklamp, and call `use desklamp 1` while next to it; taking the desklamp usually returns `Nothing happens`, and using it from another location also fails.

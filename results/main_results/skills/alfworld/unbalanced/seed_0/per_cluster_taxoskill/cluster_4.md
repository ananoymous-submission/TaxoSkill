# General guidance

- Use the observation text to confirm object presence; if a candidate lacks the exact target type (reports `nothing` or only unrelated objects), move to the next candidate rather than retrying the same location.
- If the receptacle is closed, open it before inspecting or taking from it.
- If `go to <receptacle>` returns `Nothing happens`, do not retry the same `go to`; the target is often already in range, so try `open`, `examine`, or the desired direct action from the current location.
- If `open` returns `Nothing happens`, treat the receptacle as already open/surface and proceed with `take` or `put` without re-opening.
- Take the target object with exact arguments: `take <object> <id> from <receptacle> <id>`.
- Match the task noun literally; ALFRED distinguishes `cup` from `mug`, `soapbar` from `soapbottle`, and similar categories.
- Use the exact object and receptacle ids shown in the latest observation or admissible commands for the rest of the episode unless an id becomes unavailable.
- ALFRED agents generally carry only one item at a time.
- Track whether receptacles are open or closed from observations; once a container is opened, it usually stays open on later visits, so do not re-open it.
- After checking the most likely source for the object category, scan visible open surfaces such as countertops and the sinkbasin before systematically opening every closed cabinet or drawer; closed storage costs extra steps to open and inspect.

# Task-specific guidance

For lamp-examination tasks such as `look at <object> under the <lamp>` or `examine <object> with the <lamp>`, take the target object, go to the lamp, and `use <lamp> <id>`; no final `put` is required.

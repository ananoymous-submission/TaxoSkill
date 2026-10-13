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

## Clean and Place

- Parse the task into target object type, required state (`clean`), and destination category.
- Carry the object to a sink or bathtub basin and apply the state change directly: `clean <object> <id> with <sinkbasin or bathtubbasin> <id>`.
- For clean tasks, treat the sinkbasin as a high-value source and check it before closed cabinets and drawers unless the target object has already been found.
- If you realize you picked the wrong subtype, immediately correct and process the exact requested object before final placement.
- Plan multi-object tasks as repeated one-object trips.
- If a second `take` returns `Nothing happens`, check `inventory`; if the first object is still held, deliver it before returning for the next.
- After delivering the first object, return to the source location and take the remaining instance from where it was last observed.
- Track placed objects. When you return to a destination after delivering one of multiple items, expect to see the already-delivered object there and plan the next placement around that current state.
- Go to the destination category. If the destination is a closed drawer, cabinet, fridge, or microwave, open it before placing.
- Finish with `put <object> <id> in/on <destination> <id>`, using the literal `in/on` form; `put <object> <id> in <destination> <id>` or `put <object> <id> on <destination> <id>` alone can fail even when the destination is open.
- When you open the final destination, read the observation for objects already on/in it. If the destination is already occupied, be prepared for the final `put` to fail.
- If `put <object> <id> in/on <destination> <id>` returns `Nothing happens`, put the carried object down on a nearby open surface, move the blocking object out of the destination, then pick the target object back up and finish the placement.

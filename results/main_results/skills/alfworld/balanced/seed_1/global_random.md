

## Follow a minimal retrieve-transform-place goal loop for ALFWorld/ALFRED tasks
- Parse the task into target object(s), required transformation (if any), and destination.

- Preserve the exact object type named in the task (`cup`, `plate`, `book`, `creditcard`); do not substitute a similar object such as a mug for a cup, even if it is found first.

- If the destination is named only by type (`shelf`, `cabinet`, `countertop`, `diningtable`), choose a currently listed instance such as `shelf 1` and use that exact ID for navigation and `put`. Any listed instance of the destination type is usually acceptable unless a specific ID is specified.
- Find the target object first, apply any required transformation, then go to the destination and put the object in/on it.
- Start with the most likely location; avoid opening or visiting unrelated containers unless the target is not found.
- Execute exactly one action, wait for the observation, and use the latest observation to decide the next action.
- Once the goal action reports success, stop; do not issue extra `look`, `inventory`, or verification actions.

## Use exact observed IDs and environment-accepted command syntax
- Always copy object and receptacle IDs from the current observation (e.g. `apple 3`, `plate 2`); do not rely on memory or substitute generic nouns.
- Use the accepted command forms: `take <object> <id> from <surface/receptacle>`, `put <object> <id> in/on <receptacle> <id>`, and `<cool|heat|clean> <object> <id> with <appliance> <id>`.
- Match the environment's required form exactly rather than prose variants.

## Open closed containers and respect the one-object carry limit
- Before `take <item> from <container>` or `put <item> in/on <container>`, open the container if it is closed and closable (drawer, cabinet, microwave, fridge).

- For `cool`, `heat`, or `clean`, apply the command while still holding the target object. For closed closable appliances such as fridges and microwaves, open the appliance first; opening is sufficient, so do not place the object inside or close the appliance before transforming.

- Match each transformation to its correct appliance: use `fridge` for `cool`, `microwave` for `heat`, and `sinkbasin` for `clean`. If the current admissible actions show the wrong transformation for the current appliance (e.g. `heat apple 1 with microwave 1` when the task requires `cool`), go to the correct appliance instead of substituting a different transformation or retrying the failed one.
- Carry only one object at a time. If `take` returns `Nothing happens`, check `inventory`; if already holding another object, put it down or deliver it before retrying.
- For goals such as `put two plate`, locate and place exactly two distinct object instances, delivering one at a time while tracking the count.

## Prefer likely object locations and limit search
- Prefer counters/dining tables for food and dishes, fridge for perishables, drawers/desks for stationery/utensils, and shelves/sidetables for small objects.
- Pick one plausible surface/container from the initial observation and try it first.

- Before exhaustive search, check the current admissible actions for `take <target> <id> from <receptacle>`; if present, go directly to that receptacle to retrieve the target.
- Move on from empty or wrong-object locations rather than revisiting them; stop searching once the needed number of object instances is found.

<!-- SLOW_UPDATE_START -->
Always preserve the exact object type named in the task (`cup`, `plate`, `book`, `cloth`, `creditcard`); never take a similar object such as a towel for a cloth or a mug for a cup, even if it appears first.

Before every `take`, verify from the current observation that the object and receptacle match the task target exactly. If the visible object is not the target, leave it and keep searching.

When searching for a target, first use the current admissible actions. If you see an admissible action of the form `take <target> <id> from <receptacle>`, go directly to that receptacle and use it rather than wandering through unrelated receptacles.

If the target is not visible after checking likely locations, broaden the search across other probable container types (cabinets, drawers, shelves, fridge). Do not assume an object cannot be in an unusual container; for example, a plate can be inside a fridge. Avoid rigidly exhausting every instance of one receptacle type before switching to another likely type.

For `cool`, `heat`, or `clean`:
- Apply the transformation while still holding the target object.
- For closed appliances such as fridges and microwaves, open the appliance first; opening is sufficient.
- Do NOT place the object inside the appliance or close the appliance before transforming. After opening, issue `<cool|heat|clean> <object> <id> with <appliance> <id>` while holding the object.

Use environment command syntax exactly:
- For placing objects, issue the literal command `put <object> <id> in/on <receptacle> <id>` with `in/on` as a single token.
- Do not replace `in/on` with only `in` or only `on` unless the current admissible action explicitly shows that exact form.

If a command returns `Nothing happens`:
- For a failed `take`, check `inventory`; if you are already holding another object, put it down or deliver it before retrying.
- For a failed `put`, try the literal `in/on` form and check admissible actions for the exact accepted command instead of repeating the same `in`/`on` variant.
- For a failed transformation, verify you are holding the target and that the closed appliance is open; do not retry the same failed command without changing the state.

When searching, move on from empty or wrong-object locations rather than revisiting them. For multi-object goals such as `put two plate`, track distinct object instances and deliver them one at a time.

Once the goal action reports success, stop immediately; do not issue extra `look`, `inventory`, or verification actions.
<!-- SLOW_UPDATE_END -->

# General guidance

## Task completion and stopping criteria
- Hard stop after a successful final `put`: once the final object is placed in the requested destination and the observation begins with `You put ...`, the task is solved. Do **not** call `act` again; no `look`, `examine`, `inventory`, `close`, or navigation action may be emitted after that confirmation, even to verify or tidy up.
- Do not issue any `look`, `examine`, `inventory`, or `close` after the final placement. The success observation from the final `put` (e.g., `You put ... in/on ...`) is the completion signal, and no further verification is required.
- If your reasoning says the task is complete, stop immediately and do not turn that thought into another `look`, `examine`, `inventory`, or `close` action. Closing the destination container after the final placement is unnecessary unless the task explicitly asks for it.
- Repeated confirmation loops waste steps and cause premature truncation, even when the task is already solved.

## Search efficiency and handling `Nothing happens`
- Before exhaustively opening cabinets and drawers, check open surfaces such as countertops, shelves, tables, sinkbasins, and coffeetables; many target objects are visible there.
- An initial `look` from the room center often reports `you see nothing` even when many objects are on nearby surfaces. Treat this as non-informative and visit candidate surfaces directly instead of retrying `look`.
- Use room context to prioritize open surfaces: in bathrooms check the toilet, toiletpaperhanger, sinkbasin, bathtubbasin, and towel/handtowel holders; in living rooms/offices check coffeetables, sidetables, desks, and dressers before closed cabinets/drawers.
- Prefer likely locations by object type and task (e.g., food objects on countertops/in the fridge, small objects in drawers/on tables), then return to open surfaces rather than opening every remaining cabinet/drawer in order.
- For tasks phrased as `some X` (e.g., `heat some plate`), any instance is acceptable. Pick up the first X found and proceed; do not continue searching for a specific or "better" X.
- When a closed container/appliance is a likely location or the requested destination (e.g., cabinet, fridge, safe, drawer, microwave), open it once before checking its contents or placing an object inside. Arrival text like `The fridge 1 is closed` or `The cabinet 1 is closed` means the container needs opening, not that it is empty.
- If a command returns `Nothing happens`, do not repeat the same command multiple times. Change one factor: inspect `inventory`, use `look` to see the current location, verify whether a container is open or closed, or try a different nearby surface.

## Moving multiple objects
- ALFWorld agents can usually carry only one object at a time.
- Before attempting to take a second object, check `inventory`. If a `take` returns `Nothing happens` while something is already carried, do not conclude the target is unpickupable and do not retry the same `take` immediately.

# Task-specific guidance

## Moving multiple objects
- If you are carrying an object that is not the exact requested type and a `clean`, `heat`, `cool`, or `put` returns `Nothing happens`, do not keep retrying that object. Return it to the holder/surface where you found it, then search for and take the exact object type named in the task.
- For `find two X and put them in/on Y` or `put two X in/on Y` tasks, move the objects one at a time: take the first object to the destination and put it there, then return for the second object and put it there as well. Avoid trying to carry both and avoid swap-staging objects on intermediate surfaces.

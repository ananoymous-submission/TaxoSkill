

## ALFWorld command and container handling

- Reuse the exact object and location IDs from the current observation in every command (e.g., `take cellphone 2 from dresser 1`, `put pan 1 in/on stoveburner 1`).
- Use the full `put <object> <id> in/on <destination> <id>` form. Omitting `in/on` can return `Nothing happens`.

- Do not try `put <object> <id> in <destination> <id>` or `put <object> <id> on <destination> <id>` separately; use the literal `in/on` form on the first attempt for every destination, including toilets and drawers.
- Open a closed container before taking from it or placing an object into it (e.g., drawer, cabinet, fridge, microwave).

- If `open <container>` returns `Nothing happens`, do not retry the same open; treat the container as already open and continue with the intended `take` or `put`.
- For clean/cool/heat tasks, follow: `take <object> from <location>` -> `go to <appliance>` -> `clean/cool/heat <object> with <appliance>` -> `go to <destination>` -> `put <object> in/on <destination>`.

## Efficient ALFWorld search

- Search by decision-level ordering before opening closed cabinets or drawers. In kitchen scenes: check the fridge first for food/cool items, then countertops, then quick visible surfaces such as sinkbasin, stoveburner, toaster, coffeemachine, and garbagecan, then closed cabinets/drawers. In non-kitchen rooms, search visible surfaces (tables, sofas, armchairs, shelves) before closed furniture. For egg tasks, check sinkbasin immediately after the fridge and countertops.
- Do not search containers in numeric order. Track which receptacles you have already checked and avoid revisiting them.
- Treat common task categories by any plausible instance: for example, when the task asks for a cup, a mug is an acceptable cup.

## Heating, cooling, and cleaning objects

- For `heat`, `cool`, and `clean` tasks, use the transform command directly on the held object at the appliance, e.g. `heat <object> with microwave 1`.
- Do not open the appliance and place the object inside simply to heat or cool it. If a command returns "Nothing happens", first check whether the object is held, the target is correct, and any required container is already open.

## Multi-object delivery and carrying capacity

- If a task requires moving more than one object, deliver the currently held object to the destination before retrieving the next one.
- If `take <object> from <location>` returns "Nothing happens" while you are already carrying something, do not retry the same take repeatedly: put or deliver the held item first.
- Do not place a needed object in an intermediate location merely to free your hands unless the task requires that intermediate step.

## Stopping and no-op prevention

- Stop immediately after a successful `put <object> <id> in/on <destination> <id>` when that put completes the task objective. Do not close the container, and do not call `look`, `inventory`, or `examine` afterward.
- If `go to <location>` returns `Nothing happens`, do not retry the same `go to` command. Treat the location as reachable/current and continue with the intended `open`, `take`, or `put`.

<!-- SLOW_UPDATE_START -->
<!-- SLOW_UPDATE_END -->

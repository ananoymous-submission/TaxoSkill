# General guidance

## Environment guidance

### Actions, object naming, and ambiguity
- Use only exact action verbs shown by the environment, e.g. `pick up OBJ`, `move OBJ to OBJ`, `pour OBJ into OBJ`, `open OBJ`, `look at OBJ`, `focus on OBJ`, `dunk OBJ in OBJ`, `connect ...`, `disconnect ...`, `activate ...`. Do not use unsupported verbs such as `take`.
- Liquids and powders are usually not picked up directly. Pick up their container, or use `pour`/`dunk` to transfer them.
- When the environment returns an ambiguous-request numbered menu, respond with only the number of the intended option (e.g. `0`). Do not combine the number with an action or object phrase. Use the location text in each option (e.g. `in inventory`) to select the correct referent.
- When moving containers with duplicate names, use the disambiguation prompt to select the one holding the substance of interest.

### Observations, inventory, and stale names
- After time passes or objects are moved/mixed, run `look around` or `look at CONTAINER` to refresh object names and locations. Commands that use stale object names often fail with `No known action matches that input`.
- `focus on OBJ` only succeeds when the target object is visible in the current room or carried. If it returns `No known action matches that input`, teleport to the room containing the object or `pick up` the object first, then retry the focus in the required order.

### Navigation and search
- Start by teleporting to the room named in the task, then use `look around` immediately to see available objects.
- Use common room knowledge to reduce blind search: thermometers, stoves/ovens/freezers, and seed jars are often in the kitchen; animals and eggs are often outside; flower pots with soil/water are often in the greenhouse.
- If a required object is not visible in the current room, search other rooms systematically with `look around`, opening and inspecting closed containers where relevant.

## Execution discipline

- Stopping and `step_budget`: when the task is complete, stop; spend and preserve steps within the `step_budget` and avoid loops or repeated failed actions.
- Perform `focus on OBJ` instructions in the exact order given by the task before taking manipulative actions on the target.
- If an instrument such as a thermometer is located in another room, first `pick up` the instrument, then teleport to the target, then `use instrument on target`.
- To deliver an object to a container or surface, `pick up` the object first if it is not already in inventory, then teleport to the destination and `move OBJ to OBJ`.
- Re-inspect an object or container after time passes or after objects are moved/mixed.

# Task-specific guidance

## Recipe-Based Substance Creation

### Combining and mixing
- Follow the recipe's operation order and the task's focus wording. If the task has an ordered `part-way done` focus step, focus on the intermediate substance as soon as that first mix is complete, before doing anything further or focusing the final product.
- Use content-qualified names in `pour` while the cups/containers are still in the room, e.g. `pour wood cup containing yellow paint into wood cup containing blue paint`. Avoid bare duplicate commands like `pour wood cup into wood cup` once both cups have been picked up; they produce large ambiguous menus and `can't move something into itself`.
- After pouring, the target container's name changes to a comma-separated contents list (e.g. `wood cup containing red paint, yellow paint`). That full string often fails; run `look around` or `look at inventory`, then use `mix wood cup` and pick the container whose inspected contents show both paints.
- After mixing, refresh again and `focus on` the newly named paint substance (`focus on orange paint` / `focus on green paint`), not the container (`focus on wood cup containing green paint`).
- If a comma-separated container name fails in `mix`/`pour`, refresh with `look around` or `look at inventory`, then use `mix wood cup` and pick by location. If a numbered option returns `No known action matches that input`, do not retry the same number; inspect another option or use `mix wood cup containing orange paint and red paint` with `and` instead of a comma.

### Paint and colour rules
- Primary-colour mixing: red + yellow = orange, blue + yellow = green, red + blue = purple. For `red-orange paint` tasks, mixing red and yellow usually produces the required/intermediate orange; follow the task's focus wording to decide whether to stop at orange or continue per instructions.
- For red-orange paint: focus on `orange paint` immediately after the first red+yellow mix; after the final orange+red mix, the substance is `red-orange paint`, so focus on `red-orange paint` as the final focus.
- Search the art studio, workshop desks, and paint cupboards first for wood/tin cups of red/yellow/blue paint. Do not spend many actions opening kitchen drawers/cupboards when the art studio has the named paint cups.

### Heating, cooling, and water transfer
- For heating/cooling state-change tasks, open/activate the device, move the substance (usually in its container) into or onto it, close if needed, wait, reopen the device if closed, then measure or examine progress. If `use thermometer on SUBSTANCE` returns `No known action matches that input`, try `use thermometer on CONTAINER` (the vessel holding the substance).
- For melting-point tasks, do not mistake the current/ambient thermometer reading for the melting point. Heat the substance until it melts, then compare its known/observed melting point against the threshold; deactivate the heat source before the final focus/placement.
- For boiling: heat the liquid in a container on an activated stove/oven, then wait in small increments (`wait1` or one `wait`) and immediately check the container/room. Look for `steam` inside the container. Do not let the liquid boil away to empty; if the container becomes empty before you focus on steam, you have waited too long.
- For freezing: keep the freezer/device door closed during every wait. Open only for a quick check, and if more time is needed, close it again before waiting. Never wait with the freezer door open. If the temperature is below 0°C but the substance name has not changed, close the door and wait another small block, then inspect once.
- When transferring water from a fixed source such as a toilet, use `dunk CONTAINER in SOURCE` if `pour water into CONTAINER` reports the source is not movable.

### Stopping rule
- Stop when the final recipe step is complete and the final required `focus on` or placement has been performed.

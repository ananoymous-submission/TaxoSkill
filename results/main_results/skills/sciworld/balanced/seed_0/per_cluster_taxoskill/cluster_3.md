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

## State-Change Task Guidance

- For heating or cooling state-change tasks, open or activate the device, move the substance (usually in its container) into or onto the device, close it if needed, wait, reopen the device if closed, then measure or examine progress.
- If `use thermometer on SUBSTANCE` returns `No known action matches that input`, try `use thermometer on CONTAINER` (the vessel holding the substance).

### Melting
- Heat the substance until it melts.
- Do not mistake the current/ambient thermometer reading for the melting point. Compare the known or observed melting point against any task threshold, and deactivate the heat source before the final focus or placement.

### Boiling
- Heat the liquid in a container on an activated stove or oven.
- Wait in small increments (`wait1` or one `wait`) and immediately check the container or room. Look for `steam` inside the container.
- Do not let the liquid boil away to empty. If the container becomes empty before you focus on steam, you have waited too long.

### Freezing
- Keep the freezer/device door closed during every wait. Open only for a quick check, and if more time is needed, close it again before waiting. Never wait with the freezer door open.
- If the temperature is below 0°C but the substance name has not changed, close the door and wait another small block, then inspect once.

### Combustion
- If combustion is required, apply the same heating procedure: heat the substance in or on an activated heat source until it combusts, then deactivate the heat source and focus on the substance.

### Transferring liquids from fixed sources
- When transferring water from a fixed source such as a toilet, use `dunk CONTAINER in SOURCE` if `pour water into CONTAINER` reports the source is not movable.

### Final Focus
- Complete the required state change before the final `focus on SUBSTANCE`. If focus fails because the substance name changed, refresh with `look around` or `look at CONTAINER`, then focus on the updated substance name.
- Stop after the final required focus on the transformed substance succeeds; do not keep waiting once the target state is reached.

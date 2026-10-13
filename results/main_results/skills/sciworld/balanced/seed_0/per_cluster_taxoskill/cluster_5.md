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

## Life Stage Ordering

### Locate organisms and identify current stage
First locate all relevant organisms/plants and identify each object's current stage from `look around` or `examine` (e.g. seed, seedling, juvenile, adult, reproducing, dead).

For find, move, or compare organism tasks, treat visible immature stages such as eggs, seeds, larvae, and seedlings as valid organisms. Do not reject an egg or seed because it is not an adult; if the task asks for an animal and eggs/immature organisms are visible, focus on the most relevant one before exhaustively searching other rooms.

### Focus stages in earliest-to-latest order
If the task requires focusing on several life stages in earliest-to-latest order, focus on each stage as soon as it appears. Earlier stages can hatch/grow and disappear; do not wait until the organism reaches the final stage before trying to focus on earlier ones.

After focusing/observing, wait in small blocks (`wait1` or `wait`) and check the same location with `look around` or `examine` to catch the next stage.

Stop when each requested stage has been focused in chronological order from earliest to latest; do not continue waiting or refocusing stages after the final required focus is complete.

### Plant and pollinator growth
For plant growth, move the seed into a flower pot if `move seed to soil` is rejected, then add or ensure soil and water. Greenhouse/outside light is usually sufficient; do not waste actions hunting for a lamp. Wait and examine the growing plant each block until the requested reproduction stage.

If pollination is required, inspect/use the available pollinator or pollinator-related object (e.g. bee hive) instead of spending many steps searching for extra containers.

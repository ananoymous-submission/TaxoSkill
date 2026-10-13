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

## Electrical Conductivity Testing

- Examine each electrical component first to learn its connection points. Wires and some test objects use `terminal 1`/`terminal 2`; batteries, bulbs, and switches usually use `anode`/`cathode`. Always name these contacts in `connect` and `disconnect` commands.
- Build one closed series circuit using **two wires** so the return path goes through a wire, not directly from the bulb/buzzer back to the battery. Example: `connect black wire terminal 1 to battery anode` → `connect black wire terminal 2 to orange light bulb anode` → `connect orange light bulb cathode to blue wire terminal 1` → `connect blue wire terminal 2 to battery cathode`. For conductivity tests, insert the test object between one wire and the bulb (e.g. `connect black wire terminal 2 to metal fork terminal 1` → `connect metal fork terminal 2 to orange light bulb anode`) while keeping the second wire as the return path. A one-wire setup with a direct component-to-battery connection often leaves the bulb/buzzer off and causes unproductive rebuild/switch-adding loops; always include the return wire before judging the circuit.
- Optionally include a switch if one is available. A switch is not required to light a bulb; if a switch is in the circuit, use `activate switch` and then re-examine the bulb/buzzer.
- If a bulb/buzzer that should work remains off, `examine` each component to trace missing or improper connections rather than rebuilding the circuit, trying to activate the battery, or adding a switch unnecessarily.
- Use `disconnect OBJ` (e.g. `disconnect black wire`) to clear a whole object's connections; it may clear multiple connections, so reconnect all affected parts explicitly before testing again.
- Before concluding an object is nonconductive, verify the circuit with a known conductor/control and rule out wiring mistakes.
- After finishing the two-wire series circuit, run `wait1`, then `examine` the bulb/buzzer. Do not judge conductivity before this tick.
- If the bulb/buzzer is on, the object is conductive; immediately move it to the conductive box.
- If the bulb/buzzer is off, run one focused trace with `examine` on the battery, wires, bulb/buzzer, and test object. If the path is complete (battery anode → first wire → [test object] → bulb/buzzer → second wire → battery cathode), classify the object as nonconductive and move it to the nonconductive box.
- Do not rebuild the circuit or search for a known conductor/control when the circuit trace is complete and the bulb/buzzer is off. Do not activate the battery or add a switch in that situation. This overrides the general 'verify with a known conductor' step for completed circuits.
- For conditional placement tasks like conductivity tests, use the test result first, then pick up the object and move it into the box indicated by the result.

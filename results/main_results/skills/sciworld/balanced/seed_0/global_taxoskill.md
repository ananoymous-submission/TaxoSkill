

### Navigation and Orientation
- Start by teleporting to the room named in the task, then use `look around` immediately to see available objects.

- Use common room knowledge to reduce blind search: thermometers, stoves/ovens/freezers, and seed jars are often in the kitchen; animals and eggs are often outside; flower pots with soil/water are often in the greenhouse.
- If a required object is not visible in the current room, search other rooms systematically with `look around`, opening and inspecting closed containers where relevant.

### Ordered Focus and Task Execution
- Perform `focus on OBJ` instructions in the exact order given by the task before taking manipulative actions on the target. `focus on OBJ` only succeeds when the target object is visible in the current room or carried; if it returns `No known action matches that input`, teleport to the room containing the object or `pick up` the object first, then retry the focus in the required order.

### Tool Use and Object Relocation
- If an instrument such as a thermometer is located in another room, first `pick up` the instrument, then teleport to the target, then `use instrument on target`.
- To deliver an object to a container or surface, `pick up` the object first if it is not already in inventory, then teleport to the destination and `move OBJ to OBJ`.

- For measurement-based conditional tasks (e.g. place an object in one box if above a threshold, another if below), use the instrument and read the measurement first, then pick up the object and move it into the container indicated by the threshold.
- When moving containers with duplicate names, use the disambiguation prompt to select the one holding the substance of interest.

### State-Change Monitoring and Attribute Comparisons
- For heating/cooling state-change tasks, open/activate the device, move the substance (usually in its container) into or onto it, close if needed, wait, reopen the device if closed, then measure or examine progress. If `use thermometer on SUBSTANCE` returns `No known action matches that input`, try `use thermometer on CONTAINER` (the vessel holding the substance).
- For melting-point tasks, do not mistake the current/ambient thermometer reading for the melting point. Heat the substance until it melts, then compare its known/observed melting point against the threshold; deactivate the heat source before the final focus/placement.
- When object attributes such as life span are not textually described, rely on reliable general knowledge for comparisons and then focus on the chosen object.

## ScienceWorld Operational Playbook

### Action grammar and disambiguation
- Use only exact action verbs shown by the environment, e.g. `pick up OBJ`, `move OBJ to OBJ`, `pour OBJ into OBJ`, `open OBJ`, `look at OBJ`, `focus on OBJ`, `dunk OBJ in OBJ`, `connect ...`, `disconnect ...`, `activate ...`. Do not use unsupported verbs such as `take`.
- Liquids and powders are usually not picked up directly. Pick up their container, or use `pour`/`dunk` to transfer them.
- When the environment returns an ambiguous-request numbered menu, respond with only the number of the intended option (e.g. `0`). Do not combine the number with an action or object phrase. Use the location text in each option (e.g. `in inventory`) to select the correct referent.
- After time passes or objects are moved/mixed, run `look around` or `look at CONTAINER` to refresh object names and locations. Commands that use stale object names often fail with `No known action matches that input`.

### Multi-stage life-cycle and plant-growth tasks
- First locate all relevant organisms/plants and identify each object's current stage from `look around` or `examine` (e.g. seed, seedling, juvenile, adult, reproducing, dead).

- For find/move/compare organism tasks, treat visible immature stages such as eggs, seeds, larvae, and seedlings as valid organisms. Do not reject an egg or seed because it is not an adult; if the task asks for an animal and eggs/immature organisms are visible, focus on the most relevant one before exhaustively searching other rooms.
- If the task requires focusing on several life stages in earliest-to-latest order, focus on each stage as soon as it appears. Earlier stages can hatch/grow and disappear; do not wait until the organism reaches the final stage before trying to focus on earlier ones.
- After focusing/observing, wait in small blocks (`wait1` or `wait`) and check the same location with `look around` or `examine` to catch the next stage.
- For plant growth, move the seed into a flower pot if `move seed to soil` is rejected, then add or ensure soil and water. Greenhouse/outside light is usually sufficient; do not waste actions hunting for a lamp. Wait and examine the growing plant each block until the requested reproduction stage.
- If pollination is required, inspect/use the available pollinator or pollinator-related object (e.g. bee hive) instead of spending many steps searching for extra containers.

### Electrical circuits and conductivity testing
- Examine each electrical component first to learn its connection points. Wires and some test objects use `terminal 1`/`terminal 2`; batteries, bulbs, and switches usually use `anode`/`cathode`. Always name these contacts in `connect` and `disconnect` commands.
- Build one closed series circuit using **two wires** so the return path goes through a wire, not directly from the bulb/buzzer back to the battery. Example: `connect black wire terminal 1 to battery anode` → `connect black wire terminal 2 to orange light bulb anode` → `connect orange light bulb cathode to blue wire terminal 1` → `connect blue wire terminal 2 to battery cathode`. For conductivity tests, insert the test object between one wire and the bulb (e.g. `connect black wire terminal 2 to metal fork terminal 1` → `connect metal fork terminal 2 to orange light bulb anode`) while keeping the second wire as the return path. A one-wire setup with a direct component-to-battery connection often leaves the bulb/buzzer off and causes unproductive rebuild/switch-adding loops; always include the return wire before judging the circuit.
- Optionally include a switch if one is available. A switch is not required to light a bulb; if a switch is in the circuit, use `activate switch` and then re-examine the bulb/buzzer.
- If a bulb/buzzer that should work remains off, `examine` each component to trace missing or improper connections rather than rebuilding the circuit, trying to activate the battery, or adding a switch unnecessarily.
- Use `disconnect OBJ` (e.g. `disconnect black wire`) to clear a whole object's connections; it may clear multiple connections, so reconnect all affected parts explicitly before testing again.
- Before concluding an object is nonconductive, verify the circuit with a known conductor/control and rule out wiring mistakes.

### Chemistry / paint-mixing tasks
- Primary-colour mixing: red + yellow = orange, blue + yellow = green, red + blue = purple. For "red-orange paint" tasks, mixing red and yellow usually produces the required/intermediate orange; follow the task's focus wording to decide whether to stop at orange or continue per instructions.
- Search the art studio, workshop desks, and paint cupboards first for wood/tin cups of red/yellow/blue paint. Do not spend many actions opening kitchen drawers/cupboards when the art studio has the named paint cups.
- Prefer content-qualified names in `pour` while the cups are still in the room, e.g. `pour wood cup containing yellow paint into wood cup containing blue paint`. Avoid bare duplicate commands like `pour wood cup into wood cup` once both cups have been picked up; they produce large ambiguous menus and "can't move something into itself".
- After pouring, the target container's name changes to a comma-separated contents list (e.g. `wood cup containing red paint, yellow paint`). That full string often fails; run `look around` or `look at inventory`, then use `mix wood cup` and pick the container whose inspected contents show both paints.
- After mixing, refresh again and `focus on` the newly named paint substance (`focus on orange paint` / `focus on green paint`), not the container (`focus on wood cup containing green paint`).
- If the task has an ordered "part-way done" focus step, focus on the intermediate substance as soon as that first mix is complete, before doing anything further or focusing the final product.

<!-- SLOW_UPDATE_START -->
### Strategic Guardrails (epoch update)

#### Life-span and attribute comparisons
- Compare by species, not by life stage. Eggs, seeds, larvae, and juveniles represent the adult organism's species for life-span/attribute questions; do not choose an egg or immature form simply because it is immature.
- For the common outdoor animal set, use this shortest-to-longest lifespan order: baby hedgehog < frog < giant tortoise. If the task asks for the shortest life span and a baby hedgehog is visible, focus on the baby hedgehog.

#### State-change tasks
- For boiling: Heat the liquid in a container on an activated stove/oven, then wait in small increments (`wait1` or one `wait`) and immediately check the container/room. Look for `steam` inside the container. Do not let the liquid boil away to empty; if the container becomes empty before you focus on steam, you have waited too long.
- For freezing: Keep the freezer/device door closed during every wait. Open only for a quick check, and if more time is needed, close it again before waiting. Never wait with the freezer door open. If the temperature is below 0°C but the substance name has not changed, close the door and wait another small block, then inspect once.
- When transferring water from a fixed source such as a toilet, use `dunk CONTAINER in SOURCE` if `pour water into CONTAINER` reports the source is not movable.

#### Electrical conductivity decisions
- After finishing the two-wire series circuit, run `wait1`, then `examine` the bulb/buzzer. Do not judge conductivity before this tick.
- If the bulb/buzzer is on, the object is conductive; immediately move it to the conductive box.
- If the bulb/buzzer is off, run one focused trace with `examine` on the battery, wires, bulb/buzzer, and test object. If the path is complete (battery anode → first wire → [test object] → bulb/buzzer → second wire → battery cathode), classify the object as nonconductive and move it to the nonconductive box.
- Do not rebuild the circuit or search for a known conductor/control when the circuit trace is complete and the bulb/buzzer is off. Do not activate the battery or add a switch in that situation. This overrides the general 'verify with a known conductor' step for completed circuits.

#### Paint mixing finalization
- If a comma-separated container name fails in `mix`/`pour`, refresh with `look around` or `look at inventory`, then use `mix wood cup` and pick by location. If a numbered option returns `No known action matches that input`, do not retry the same number; inspect another option or use `mix wood cup containing orange paint and red paint` with `and` instead of a comma.
- For red-orange paint: focus on `orange paint` immediately after the first red+yellow mix; after the final orange+red mix, the substance is `red-orange paint`, so focus on `red-orange paint` as the final focus.
<!-- SLOW_UPDATE_END -->

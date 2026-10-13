

## Sequential find/focus/move tasks
When a task says 'find a(n) X. First, focus on X. Then, move it to Y':
1. Identify an object matching the requested type (for example 'living thing' or 'plant'). Prefer objects described by their object type (e.g. 'apple tree', 'pea plant', 'bee') over their containers (e.g. 'flower pot 7', 'bee hive').
2. Follow the required order: first `focus on <target object>`, then pick it up if it is not in your inventory, then `move <target object> to <destination>`.
3. For an object inside a container, use the object's name in `focus on ...`, `pick up ...`, and `move ...`, not the container's name, unless the task explicitly asks for the container.
4. Do not stop after `focus on ...`; focus alone is not completion. Always perform the requested move.
5. When the environment asks for numeric disambiguation, select the option that names the actual target object and matches the described location/contents.

## Verification and time management
- After a successful move action, accept the environment's confirmation unless the next observation unambiguously shows failure. Avoid repeated `examine`/`look around` loops and avoid unnecessary `wait` actions; they consume limited steps and living things may die or change state.
- If you do verify, verify once. If the destination unexpectedly lacks the object, retry moving the same object reference instead of switching to a different object.

## Measuring phase-change properties
- A `use thermometer on X` reading reports the object's current temperature, not automatically its melting/boiling point. For a melting-point or boiling-point task, first cause the phase change (for example by heating or cooling the substance) and measure during/after the transition.
- Compare a threshold to a true phase-change temperature only after you have evidence of that transition.

- For direct current-temperature sorting tasks (e.g., `unknown substance B` with a fixed threshold), the `use thermometer on X` reading is the decision value, not a phase-change point. Compare it to the task threshold immediately; when the reading clearly satisfies one branch, do not remeasure or search for additional evidence. Then pick up X and place it in the box named by the satisfied condition (`move X to <box>`).

## ScienceWorld Execution Patterns

- After teleporting to a new room, issue `look around` before acting to locate relevant objects, containers, boxes, and appliances. Use object-category priors when choosing a room (e.g., greenhouse for plants, kitchen for food/appliances).
- For cross-room interactions, if the target object and required tool/container are in different rooms, pick up the source object or tool first (`pick up OBJ`), teleport to the destination room, and `look around` to locate the exact target before using `move OBJ to CONTAINER` or `use TOOL on OBJ`.
- Do not issue `use INSTRUMENT on OBJECT` from a room that does not contain the instrument. If a thermometer or other instrument is in another room, pick it up and carry it to the target before measuring.
- Before moving an item into a closed container or appliance (e.g., fridge, freezer), `open OBJ` first. Use `look at OBJ` after opening to confirm contents before selecting the item.
- When searching for an object whose room is unknown or category-based (e.g., animal, non-living thing), teleport and `look around` in likely rooms systematically instead of repeatedly examining the same room.

## Category selection and object reference handling
- For `find a(n) living thing`, choose a whole organism (e.g., `adult bee`, `pea plant`, `hatchling crocodile`), not detached food/plant parts such as `banana`, `apple`, or `potato`. If the current room has only ambiguous produce or non-living items, teleport to outside/greenhouse and `look around` for actual animals/plants before focusing.
- For `find a(n) animal`, check outside and greenhouse first; prefer the object type name (`adult bee`) over its container (`bee hive`).
- When the environment asks `Please enter the number...`, reply with the number alone as the next command (`0`), not `focus on OBJ 0` or `pick up OBJ 0`.
- After pickup, the inventory may rename the object (`adult bee` becomes `bee 4`). If `move <original phrase> to DEST` returns `No known action matches that input`, try the shorter base object name reported in the pickup/inventory confirmation (e.g., `move bee to DEST`, `move crocodile to DEST`) before examining or looking around.

<!-- SLOW_UPDATE_START -->
## Cross-room placement after measuring
- When a task requires you to measure a target and then place it in a box in another room, pick up the target immediately after measuring while you are still in the target's room, before teleporting to the box room. Do not teleport away and then attempt `move TARGET to BOX` while the target is still in the previous room; that produces `No known action matches that input` and wastes limited steps.
- If you do get `No known action matches that input` on a move, immediately determine where the target is, go to that location if necessary, `pick up` the target, then return and complete the move.

## Controlled heating/cooling for phase-change tasks
- When heating or cooling a substance to find a melting/boiling point, after activating the stove/freezer use the smallest wait available, such as `wait1`, not bare `wait`. A bare `wait` waits 10 iterations and can overheat organic substances such as chocolate until they catch fire.
- Measure temperature after each small wait. Once you have clear evidence that the temperature is above or below the task threshold, or that the phase has changed, stop heating/cooling and perform the required box focus or placement action.
- If you accidentally overheat a substance into a burning liquid, do not loop on `pour ... into ...` commands. Use the temperature evidence you already have to satisfy a threshold task, and proceed to the required focus or placement action.

## Creating mixed substances such as paint
- To create green paint, pour blue and yellow paint into an empty container such as a jug or empty cup, then issue `mix <container>`. After mixing, `focus on green paint` or the requested product name, not on the container object.

## Disambiguation and category selection
- If an ambiguous-object prompt asks for a numeric selection and numeric replies repeatedly fail, stop repeating the same command. Switch to another unambiguous object that satisfies the requested category and matches the task location.
- For `find a non-living thing`, prefer a clearly non-living visible object in the current or destination room, such as `painting`, rather than opening many containers and creating ambiguous references.

## Electrical conductivity testing
- In conductivity tasks, remember that metal implements such as `metal fork` or `shovel` are likely conductive. Do not accept a single unlit-bulb reading as proof of nonconductance unless you have verified the circuit completely.
- Build the test circuit using exact terminal names. First `examine battery`, `examine <wire>`, and `examine <bulb>` to learn the terminals. Then connect in series: battery anode to wire terminal 1, wire terminal 2 to object terminal 1, object terminal 2 to bulb anode, and bulb cathode to battery cathode.
- After building the circuit, check the bulb with `examine <bulb>`. If the bulb is off, inspect the battery, wires, and bulb connections and fix any missing or disconnected segment before concluding nonconductive. Do not use `activate battery`; the battery is not activatable.
<!-- SLOW_UPDATE_END -->



## Action Grammar and Disambiguation

- Use only the exact ScienceWorld action grammar. To remove an item from a container, use `pick up OBJ`; do not use forms like `take X from Y`.
- When the environment returns an `Ambiguous request` prompt asking for a number, reply with exactly the chosen option number, e.g. `0` or `1`. Do not rewrite an action with a number appended, such as `pick up apple seed 0` or `open drawer 1`.
- To prevent ambiguity when several objects share a name, include the container or location in the original command, e.g. `open drawer in cupboard`, `move apple seed in seed jar to flower pot 1`, or `look at wood cup in large cupboard`.
- Track how many identical items have already been removed, and keep containers on a surface rather than carrying them when possible.

- In an `Ambiguous request` numbered prompt, inspect the relevant area/inventory as needed (`look around`, `look at inventory`) and choose the option whose parenthetical description matches the intended location or contents (e.g. `in seed jar` vs `in inventory`, or a non-empty cup vs an empty one); do not always default to `0`.

- After resolving a numbered `Ambiguous request` for picking up one of several identical objects, verify the actual held or local referent with `look at inventory` or `look around` before the next command; the object may be renamed after pickup (e.g. `adult bee` becomes `bee 4`), so use only observed referents in later commands.

## Efficient Exploration and Tool Use

- For targets such as objects, organisms, life stages, or substances, start with `look around` in the task-named or current location and use the exact object names visible in the observation.
- Prefer focused inspection (`look around`, `examine OBJ`, `look at OBJ`) over exhaustively teleporting through rooms and opening every container. Open containers only when the target is not visible and is plausibly inside.
- Before searching many rooms for a missing substance, inspect the current and nearby rooms for tools and sources that can produce it. Use relevant tools on promising objects, e.g. a `shovel` on ground/dirt for soil or an `axe` on wood for wood.
- For ordered life-stage or focus tasks, focus on the exact stage or object names observed and in the required order.

## ScienceWorld Operational Patterns

- **State-change and appliance use**: For melting/heating tasks use the kitchen `oven` or `stove`; for freezing tasks use the `freezer`. Focus on the substance first, then open the appliance if it is closed before moving the target or container inside. Activate or close the appliance, `wait`, and verify the new state with `examine` or `look at`. For melting/boiling point measurement, use `move <container> to stove` then `activate stove`, wait, and inspect for the changed-state referent (e.g. `gallium` -> `liquid gallium`) before using the thermometer on that new referent.
- **Orient on task start**: Teleport to the room named or hinted by the task, call `look around` to survey it, and then `focus on <target>` before moving, testing, or otherwise manipulating the target.
- **Focus is not pickup**: `focus on` works on a currently visible or held referent but does not move it to inventory. To use a tool on a target in another room, `pick up` the tool first, then teleport and call `use <tool> on <target>`.
- **Search common item locations**: Match the requested category to a likely room before exhaustive search: plants/trees/seeds -> greenhouse, animals/eggs -> outside, food/beverages/recipes -> kitchen or its appliances, paints -> art studio, tools/electrical -> workshop. If a common tool, food, substance, or recipe is not in the stated room, check the kitchen via `teleport to kitchen` + `look around`; thermometers, water/ice, food items, and recipes are frequently found there or in its appliances. For animal targets, check `outside` and `greenhouse` and inspect known animal containers (e.g. `bee hive`) before opening unrelated furniture.
- **Conditional placement routine**: After measuring or testing, decide the correct container by the numeric threshold, `pick up` the target object, teleport to the room containing the boxes, and call `move <object> to <correct box>`.

- **Find-and-place routine**: For any `find X; focus on X; move X to <box>` task, select one visible target from the named category, call `focus on <target>` first, `pick up` it, teleport to the destination room, `look around` to confirm the exact destination box, then call `move <target> to <box>` and stop once the move is confirmed.
- **Recover from action failures by inspecting**: If an action fails with an unknown-action or connection error, inspect the relevant object or component with `examine` or `look at` to learn valid referents, contents, or contact points before retrying.

- **Plant growth routine**: Move seeds into a flower pot that already contains soil and water. If no pot has soil, create soil first with `use shovel on ground` outside, move the soil into a pot that already contains water, then plant the seed. In the greenhouse, natural light is sufficient; do not waste actions building an artificial light circuit. Wait, then inspect with `look at <flower pot>` or `examine <flower pot>`.
- **Fruit/pollination routine**: For fruit tasks, plant several seeds in separate pots, wait until trees reach the reproducing stage, `open bee hive`, wait again, and inspect pots until fruit (e.g. `red apple`) is visible before focusing on it.

## Electrical Conductivity Testing
- Build a closed series circuit containing the test substance, e.g. `battery -> wire -> bulb -> test substance -> battery`; a switch is optional.
- Inspect electrical components with `examine` to learn their contacts, then connect using explicit contact names such as `anode`, `cathode`, `terminal 1`, and `terminal 2`.
- Before reconnecting a component that is already connected, disconnect it first.
- Use a separate wire between each component; do not connect the bulb directly to the test object or the test object directly to the battery. The tested path should be `battery anode -> wire1 -> bulb -> wire2 -> test object -> wire3 -> battery cathode`.
- After all connections are made, verify with `examine <bulb>` and `examine <battery>`. A lit bulb indicates conductive. An off bulb indicates nonconductive only after confirming all three wire connections are present and every component is still connected. For known metal objects such as a metal pot or metal fork, treat an off bulb as a likely open circuit: rebuild with the full wire path before placing the object in the nonconductive box.
- Once the full three-wire loop is built and the bulb is off, inspect the battery, bulb, and every wire exactly once. If every listed contact is connected in a single loop and no `examine` shows `nothing`, treat the target as nonconductive: pick it up and move it to the nonconductive box. Do not disconnect the target, substitute a known conductor, swap bulbs, or rebuild a completed circuit to re-verify.
- If any `examine` after an off reading shows a missing contact, repair only that missing connection, then `examine` the bulb once. If it is still off after every contact is confirmed connected, move the target to the nonconductive box and stop.

## Handling Liquids and Paints

- **Paint mixing recipes**: orange = red + yellow; green = blue + yellow; purple = red + blue. For a tertiary paint such as yellow-green, first create the required secondary paint, `focus on` it only if the task asks for the intermediate, then add/mix the additional primary into the same non-empty cup and mix again.
- After pouring one paint cup into another, the source becomes empty and the target is renamed as containing both paints. Call `mix <container>` using only the base object name (e.g. `mix wood cup`). If it is ambiguous, choose a non-empty/dual-paint option; if that reports `That container is empty`, immediately select the next inventory option instead of retrying verbose names like `mix <container> containing X, Y`.
- After a successful paint mix, check `look at inventory` for the new paint name and `focus on <color> paint` (the substance named in the container), not the container itself.

- If the nearest sink is broken, try another room's sink (e.g. the bathroom) before searching other rooms. Do not try to pour or move water directly from a toilet; instead collect it in a cup from an activated sink.
- For food/recipe mixing tasks, read recipes by the object name shown after `titled` (e.g. `read instructions to make banana sandwich`) and combine only the named ingredients in a clean, empty container. If `mix` reports no new substance, `look at` the container and move the required ingredients to an empty container before mixing again.

- Before pouring from a jar or container, ensure the source is open. If `pour` reports the source is not open, call `open <source>` and retry the `pour`; this is common for salt/sodium-chloride jars and other closed ingredient containers.

- Never try to `pick up` a liquid directly. To collect water, activate a working sink with `activate sink`, move an empty cup or container into the sink with `move glass cup to sink`, then pick up the container.
- To transfer or mix liquids/paints, use named containers with `pour <source> into <target>` and `mix <target container>` once combined.
- When several similar cups or containers exist, specify location or contents to select the intended container.

## State-Change Completion
- Stop as soon as the requested phase appears. For melting, stop at the first melted/liquid referent (e.g. `liquid <substance>`); continuing to heat can produce `gaseous <substance>`, which is the wrong target for a melt task. For freezing, keep the appliance door closed during each `wait`; repeated opening or leaving it open can prevent the change.
- After a `wait`, a closed appliance will only show its door state when looked at, so open the appliance first, then use `look at <appliance/container>` or `look at <container>` to read contained contents. For open-area organisms or objects, use `look around` to see newly appeared stages or renamed referents. If a contained substance remains unchanged after two closed-door waits, `examine` the appliance to confirm it is active and the container/object is actually inside. If a bare substance is directly in the appliance, try moving it into an open container and repeat the closed-door wait.
- Once the correct changed-state referent is visible, perform the required `focus on` or placement with that exact referent once, then stop. Avoid repeated `focus`/`wait`/`examine` loops after the state change.

## Termination Guardrails
- After you have completed every requested `focus on`, `move`, or box placement and the observation confirms it, stop calling tools. Do not continue `wait`/`look at`/`examine`/`focus` loops to verify success.
- If the same observation repeats with no new progress, make the best final decision from existing evidence and stop.

## Knowledge and Comparison Tasks
- For life-span comparisons, classification, or other factual tasks about animals, use your built-in knowledge rather than searching for an in-world reference book; `examine` on animals usually gives only the name, not the lifespan.
- For ordered life-stage focus tasks such as `focus on the 3 life stages of X from earliest to latest`, first `look around` in the organism's current location and `focus on` every visible stage of that species in the required order. If fewer than the requested number of stages are visible, stay in that location, call `wait`, then `look around` again and focus on newly appeared stages; do not teleport through every room or open unrelated containers while waiting.

<!-- SLOW_UPDATE_START -->
## Longitudinal Strategic Control

- For factual animal comparisons and ordered life-stage focus tasks, continue using built-in knowledge rather than in-world reference books. Stay in the observed location, focus the earliest visible stage first, then wait, look around, and focus newly appeared stages of that same species in order until no required focuses remain. Do not search unrelated rooms or containers.

- For fruit/pollination growth tasks:
  - Collect exactly one seed per available flower pot. The standard greenhouse has 3 pots, so collect at most 3 seeds; do not pick up every seed in the jar.
  - Stockpile soil in a single trip outside: repeat `use shovel on ground` then `pick up soil` until you have one soil per pot. When a `pick up soil` choice appears, select the option located outside/on the ground, not an option already in inventory.
  - Teleport once to the greenhouse with all supplies, place one soil into each pot, then one seed into each pot. In ambiguous choices, select inventory items for the current move and avoid moving soil/seeds already placed in earlier pots.
  - After planting, use batched waits rather than looking after every single wait. Call `wait` twice, then `look around`; if no flowers/reproducing-stage trees are visible, wait twice again before looking. Open the bee hive only once when flowers/reproducing-stage trees are visible.
  - After the hive is open, continue batched waits. The moment any `look around` shows the requested fruit, call `focus on <fruit>` immediately and stop. Do not wait or inspect again.

- For electrical conductivity tasks:
  - After the full three-wire loop is connected, call `wait` once, then call `look at <bulb>` to determine lit/off. Do not rely on `examine <bulb>` alone for the lit/off reading.
  - If the bulb is lit, move the target to the conductive box and stop.
  - If the bulb is off, inspect the battery, bulb, and every wire exactly once. Repair any missing contact, then `wait` and `look at <bulb>` once.
  - Known metal targets such as a metal pot, metal fork, or shovel are conductive in ScienceWorld. If a known metal gives an off bulb, treat it as a circuit or observation problem. Rebuild the loop once with unused/different wires or a different bulb, wait, and look again. If the circuit is fully connected and the target is a known metal, place it in the conductive box; never send a known metal to the nonconductive box because of one off reading.
  - For unknown substances, do not classify nonconductive from a single off reading. After confirming every contact in the loop is connected and the bulb is still off, rebuild the circuit once using a different bulb or unused wires where available, then `wait` and `look at <bulb>`. Classify the unknown as nonconductive only if this verified loop is also off with every contact confirmed. If the rebuild lights, treat it as conductive. After one verified off reading, stop rebuilding and place the target in the nonconductive box.

- For freezing a solid food such as chocolate:
  - After focusing on and picking up the target, open the freezer, move the target directly into the freezer, close the door, activate if needed, and keep the door closed while waiting.
  - If you choose to use a container, first move the empty container into the freezer, then move the target into that container. Do not call `move <target> to <container>` while the container is outside the appliance; that pulls the target out of the freezer.
  - Do not open the freezer to check after every single wait. Call `wait` two or three times consecutively with the door closed, then open once and inspect the freezer or container. If the target is still unchanged after several closed-door waits, use `look around` to confirm the target/container is actually inside the appliance before continuing.
  - Once the changed-state referent is visible, focus on it once and stop. Do not continue open/close/wait/examine loops.

- For a `melt <substance>` task where the named substance is already liquid, such as `apple juice`, move its container to the stove or oven, activate the heat source, wait, and inspect. Focus on the first changed-state referent that appears exactly once, then stop. Do not move it to the freezer and do not repeatedly reopen the appliance.

- Stop immediately after completing every required focus, move, or box placement. If the same observation repeats with no new progress, make the best final decision from existing evidence and stop.
<!-- SLOW_UPDATE_END -->

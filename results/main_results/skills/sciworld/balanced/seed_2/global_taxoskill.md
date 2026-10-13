

## Task location and initial observation
- Teleport to the named room and `look around` to identify candidate objects before inspecting anything else. If the required object is not visible there, do not repeatedly `focus on` or `pick up` the absent name; teleport to a likely room for that object type (e.g., thermometer in kitchen, plants in greenhouse, animals outside) and `look around` there before acting.

- Honor task-specified focus order: when the prompt says `First, focus on X. Next, focus on Y` (or similar), issue those `focus on` commands in order before measuring, moving, or changing state. If the focus target does not yet exist or is not visible (e.g., water in a `freeze water` task), first collect/create the substance, then `focus on` it before applying the subsequent state change; do not repeatedly `focus on` an absent substance name.

## Re-observation after delays or repeated failures
- Re-run `look around` after delays or repeated reference failures. Living things can change names over time (e.g., baby → juvenile, egg → hatchling); using a stale object name causes `No known action`. Act on the latest observed object name.

- For `focus on the N life stages` tasks, do not search every room for later stages. Focus on the earliest stage seen, then `wait`, `look around` again, and focus on the newly observed stage (e.g., baby → juvenile → adult).

- For `longest`/`shortest` animal life span tasks, `examine` only restates the animal's name/life stage, not its lifespan. Use species knowledge to select the correct animal (e.g., elephants and giant tortoises live long; dragonflies live short) and then `focus on` that animal.

## Instrument-based measurements

- When a task requires `First, focus on the thermometer. Next, focus on X` and the thermometer is not in X's room, do not repeatedly focus on the absent thermometer there. Teleport to the kitchen, `focus on thermometer`, `pick up thermometer`, then teleport back to X's room before focusing on X.
- For `measure the temperature of X` tasks with bin/color boxes, use the returned thermometer reading as the decision input. Compare the reading exactly against the prompt threshold and branch (`above` vs `below`) to choose the indicated box, then immediately `pick up <target>` and `move <target> to <box>`. Do not re-measure or apply heating/cooling unless the task asks to change the temperature first.
- Fetch an instrument before measuring. If `use thermometer on <target>` or another instrument returns `No known action matches that input`, check whether the instrument is in inventory. Pick it up, teleport to the target, then retry.

## Electrical component tasks
- Connect electrical components via explicit terminals. After a generic `connect A to B` failure, `examine` each component to learn `anode`, `cathode`, `terminal 1`, and `terminal 2`. Build the circuit with full terminal names, then `activate switch` and `examine <light bulb>` to decide conductivity from the bulb state.

For conductivity tasks, treat an off bulb as nonconductive only after validating the circuit with a known conductor (e.g., a spare wire or paper clip) in place of the target and seeing the bulb light. Build a simple series loop first without a switch: `connect battery anode to light bulb anode`, `connect light bulb cathode to <object>`, `connect <object> to battery cathode` (insert wires for any leg if direct connections fail). If a metal test object does not light the bulb, re-examine the terminals, try reversing the bulb's anode/cathode connections, or add/remove the switch; do not move the target to the nonconductive box until a known conductor lights the bulb in the same setup.

## Containers, appliances, and state changes
- Open closed containers/appliances before looking inside or moving objects into them. If `move X to Y` fails because Y is not open, `open Y` and retry.
- When a target object is hidden, open plausible containers and then `look at <container>` to reveal contents before attempting to pick up the object.

- To collect a liquid, dunk an empty container into the liquid source (`move glass cup to sink`) rather than trying `move water to cup` or `pour sink into cup`; direct liquid moves usually fail with `You can't pick up a liquid directly`. If `look at` an activated sink/fountain shows nothing, move a container into/under the source, then `look at` the container to see the collected substance.
- If a heating/cooling device is broken or cannot be activated (e.g., `The stove appears broken`), switch to another device such as an oven or freezer.

- After placing a target/substance in a heater/cooler or other state-change appliance, close/activate it as needed, `wait`, then reopen/remeasure with `look at` or `examine`, and repeat waits until the required state, temperature, or life stage is reached. A single wait is often insufficient. For freezers/ovens, close the door while waiting and open it before inspecting or removing.

## Ambiguous request handling
When the environment responds with `Ambiguous request: Please enter the number for the action you intended...`, the next command must be only the number of the intended option (for example `0`). Do **not** repeat the full action with a numeric suffix such as `pick up glass cup 0`, `mix wood cup 1`, or `look at drawer 1`; those forms produce `Unknown action` or `No known action`. A bare number is only valid immediately after the menu that generated it. If you issue any other command first, get `No known action matches that input`, or want to try a different option, re-issue the ambiguous command (e.g., `mix wood cup`, `look at wood cup`) to regenerate a fresh menu before selecting a number; do not keep retrying a stale or already-failed number. Use the full menu labels, especially `(in inventory, in agent, in <room>)` vs `(in <room>)`, plus the latest `look around` / `look at` contents, to identify the intended identical container or object. Re-run `look around` after failed content-qualified commands to refresh actual container contents and ordering before choosing, because numbering can change after objects are moved or picked up.

## Relocating an object to a named destination

- Before teleporting to another room or appliance while moving an object, `pick up` the object where it currently is; only inventory travels with the agent. This includes transferring a closed container from a kitchen freezer to the workshop ultra low temperature freezer and bringing a fetched instrument back to a target room. Do not leave the original container behind.
- In tasks that end with moving an object to a named box/container, identify the destination by `look around` in the destination room before moving. Focus on the required object, pick it up, teleport to the destination, use `move <object> to <container>`, then finish with `focus on <object>` if that object is the task's focus target. Do not stop immediately after the move.
- For threshold-placement tasks, obey any `First focus on... Next focus on...` order first, measure, then branch and move to the correct box. After the move, issue a final `focus on <target>` or the measured substance name before ending.

## Final focus after substance transformations
After mixing, melting, freezing, or otherwise creating/changing a substance, inspect the container contents to learn the resulting substance name, then `focus on <resulting substance>` (e.g., `focus on orange paint`), not on the container or the original ingredients. The task usually requires the result itself rather than the vessel.

## Disambiguating identical containers by contents
When several same-named containers hold different substances, avoid bare `pick up <container>` / `pour <container> into <container>` commands that trigger large numbered menus. Instead include the contents in the command wherever a container is referenced: `pick up tin cup containing red paint`, `pour tin cup containing yellow paint into tin cup containing red paint`, `mix tin cup containing red paint`, `move glass cup containing mercury to ultra low temperature freezer`, `use thermometer on glass cup containing mercury`. If numbered options still appear, use the most recent `look around` / `look at` observations to choose the number for the intended contents, and do not keep retrying numbers that returned `No known action`.

- When the numbered options differ only by location inside parentheses, select the option whose listed source matches the intended object: after a pick-up, choose `in inventory`; when moving another duplicate seed, choose `in seed jar` over `in flower pot 1`. Avoid acting on already-planted or already-moved objects, and do not assume the same number stays correct after objects move.
- If a content-qualified container action such as `mix wood cup containing red paint` returns `No known action matches that input`, fall back to the bare object action (`mix wood cup`) and choose the numbered option whose location is `in inventory`. Then verify the result with `look at <container>` before focusing on the new substance.

## Plant-growth prerequisites
For tasks involving growing seeds, place the seed in a pot/plot with **soil**, not just water. If soil is not visible, look outside or use `use shovel on ground` to dig/place soil, then `move soil to <pot>` before or alongside watering. Then wait and `look around` repeatedly; if a seed has not changed after several waits, verify soil/water/light before waiting more.

## Fruit-bearing plant tasks
For `grow <fruit>` tasks, plant multiple seeds in separate pots with soil and water, then use short `wait` + `look around` cycles until each plant reaches the reproducing stage with a flower. Do not focus on seedlings, adult plants, or flowers as the final answer. Once flowers are present, if a bee hive is visible (e.g., in the greenhouse), `open bee hive`, then `wait` and `look around` for the target fruit on the plants. When the observation names the fruit (for example `an apple`), `focus on` that observed fruit name, not the tree, flower, or seed jar. Use `wait1` for final stage checks to avoid overshooting and running out of steps.

<!-- SLOW_UPDATE_START -->
Freezing tasks: whenever the task is to freeze a liquid, if a kitchen freezer has not produced an obvious state change after one closed-door `wait`, immediately teleport to the workshop and place the closed container in the `ultra low temperature freezer`. Open that freezer only before inserting/removing; close the door before waiting; open it once to inspect. Do not spend extra steps touring rooms such as the foundry looking for cooling devices.
For freeze/melt state-change tasks, thermometer evidence is decisive. Once the substance is below 0°C for freezing (or otherwise past the relevant transition), accept that the state change has occurred. Inspect the container once, then `focus on <target substance>` if no renamed substance is visible. Only if observation shows an explicit new name (e.g., `liquid chocolate`) should you focus on that new name. Do not keep waiting for the container text to change to wording like `frozen apple juice`.
Avoid verification loops after state changes. A closed-door `wait` followed by one `open` and one `look at`/`examine` is enough before re-focusing. If that check does not show the desired state, change the device or move to the ultra-low freezer; do not repeat the same open-check-close cycle more than twice.
Conductivity tasks: preserve the current validated pattern. Build a simple series loop, test with a known conductor (wire or paper clip) before classifying the target as nonconductive, and reverse bulb anode/cathode orientation if a known conductor does not light the bulb. Never place a target in the nonconductive box unless a known conductor lights the bulb in the same setup.
Melting-point and threshold tasks: heat or cool the target into the tested region, then use the actual comparison rule in the prompt (e.g., above vs below 50.0°C) as the decision branch. Do not infer a high final temperature equals `above the threshold` without checking the direction and the category boxes; for chocolate melting point, the correct branch is below 50.0°C.
Ambiguous menus: keep using bare numbers immediately after a menu is generated, and prefer content-qualified container commands (`glass cup containing mercury`) from the start to avoid menus. Never repeat a failed number; regenerate the menu first.
<!-- SLOW_UPDATE_END -->

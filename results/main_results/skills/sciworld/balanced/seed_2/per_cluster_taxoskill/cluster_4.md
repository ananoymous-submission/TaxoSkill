# General guidance

## Shared Guidance

## Environment guidance

### Observation, search, and navigation
- Teleport to the named room and `look around` to identify candidate objects before inspecting anything else. If the required object is not visible there, do not repeatedly `focus on` or `pick up` the absent name; teleport to a likely room for that object type and `look around` there before acting.
- Re-run `look around` after delays or repeated reference failures. Living things can change names over time; using a stale object name causes `No known action`. Act on the latest observed object name.
- When a target object is hidden, open plausible containers and then `look at <container>` to reveal contents before attempting to pick up the object.

### Containers, instruments, and inventory
- Open closed containers/appliances before looking inside or moving objects into them. If `move X to Y` fails because Y is not open, `open Y` and retry.
- Before teleporting to another room or appliance while moving an object, `pick up` the object where it currently is; only inventory travels with the agent. Do not leave the original container behind.
- Fetch an instrument before measuring. If `use thermometer on <target>` or another instrument returns `No known action matches that input`, check whether the instrument is in inventory. Pick it up, teleport to the target, then retry.

### Ambiguous requests and identical containers
- When the environment responds with `Ambiguous request: Please enter the number for the action you intended...`, the next command must be only the number of the intended option, for example `0`. Do **not** repeat the full action with a numeric suffix such as `pick up glass cup 0`; those forms produce `Unknown action` or `No known action`. A bare number is only valid immediately after the menu that generated it. If you issue any other command first, get `No known action matches that input`, or want to try a different option, re-issue the ambiguous command to regenerate a fresh menu before selecting a number; do not keep retrying a stale or already-failed number.
- Use the full menu labels, especially `(in inventory, in agent, in <room>)` vs `(in <room>)`, plus the latest `look around` / `look at` contents, to identify the intended identical container or object. Re-run `look around` after failed content-qualified commands to refresh actual container contents and ordering before choosing, because numbering can change after objects are moved or picked up.
- Prefer content-qualified container commands from the start to avoid menus. When several same-named containers hold different substances, include the contents in the command wherever a container is referenced, for example `pick up tin cup containing red paint`. If numbered options still appear, use the latest observations to choose the number for the intended contents.
- When numbered options differ only by location inside parentheses, select the option whose listed source matches the intended object, for example after a pick-up choose `in inventory`. Avoid acting on already-planted or already-moved objects, and do not assume the same number stays correct after objects move.
- If a content-qualified container action returns `No known action matches that input`, fall back to the bare object action and choose the numbered option whose location is `in inventory`; then verify the result with `look at <container>`.

## Execution discipline

### Task-specified order and instrument handling
- Honor task-specified focus order: when the prompt says `First, focus on X. Next, focus on Y` or similar, issue those `focus on` commands in order before measuring, moving, or changing state. If the focus target does not yet exist or is not visible, first collect/create the substance, then `focus on` it before applying the subsequent state change; do not repeatedly `focus on` an absent substance name.
- When an instrument or required object is absent from the current room, do not repeatedly focus on or pick up the absent name. Teleport to a likely room, `look around`, get the object or instrument, then return to the target before acting.

### Errors, loops, step budget, and stopping
- If a command is rejected with `No known action`, do not repeat the same command unchanged. Re-run `look around`, use the latest observed object name, check inventory, or open the target container/appliance before retrying.
- Avoid loops and repeated failed actions. After a required wait/action, inspect once; do not repeat the same check cycle more than twice. If the check does not show the required state, change the device or approach.
- Preserve the `step_budget`: use only the steps needed to satisfy the task, avoid unnecessary waits or extra inspections, and do not explore more rooms than needed once a required object is found.
- Stop when the task is complete: issue no further commands after the final required action, focus, or observation. Do not add extra `wait`, `look around`, `examine`, or `focus on` actions after the task condition is satisfied. If the task ends with a move or state change and a focus target is named, issue the final `focus on <target>` after that action, then stop.

# Task-specific guidance

## Plant Cultivation

### Planting prerequisites
- For tasks involving growing seeds, place the seed in a pot/plot with **soil**, not just water. If soil is not visible, look outside or use `use shovel on ground` to dig/place soil, then `move soil to <pot>` before or alongside watering.
- Then wait and `look around` repeatedly; if a seed has not changed after several waits, verify soil/water/light before waiting more.

### Life-stage checks
- For `focus on the N life stages` tasks, do not search every room for later stages. Focus on the earliest stage seen, then `wait`, `look around` again, and focus on the newly observed stage (e.g., seed → seedling → adult → flowering plant).
- Plant names can change across stages; use the latest observed object name before focusing or acting.

### Reproduction stage vs fruit target
- If the task asks to focus on the reproduction stage, continue `wait` + `look around` cycles until the plant reaches the reproducing stage with a flower, then `focus on` that flowering/reproducing plant.
- For `grow <fruit>` tasks, plant multiple seeds in separate pots with soil and water, then use short `wait` + `look around` cycles until each plant reaches the reproducing stage with a flower. Do not focus on seedlings, adult plants, or flowers as the final answer.

### Pollination and final fruit
- Once flowers are present, if a bee hive is visible (e.g., in the greenhouse), `open bee hive`, then `wait` and `look around` for the target fruit on the plants.
- When the observation names the fruit (for example `an apple`), `focus on` that observed fruit name, not the tree, flower, or seed jar.
- Use `wait1` for final stage checks to avoid overshooting and running out of steps. After focusing on the observed fruit, stop.

### Duplicate seeds and containers
- When numbered options differ only by location inside parentheses, select the option whose listed source matches the intended object: after a pick-up choose `in inventory`; when moving another duplicate seed, choose `in seed jar` over `in flower pot 1`. Avoid acting on already-planted or already-moved objects.

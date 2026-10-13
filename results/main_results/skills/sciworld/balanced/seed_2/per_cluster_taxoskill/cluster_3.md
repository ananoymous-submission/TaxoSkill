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

## State Change

### Collecting and preparing the substance
- To collect a liquid, dunk an empty container into the liquid source (`move glass cup to sink`) rather than trying `move water to cup` or `pour sink into cup`; direct liquid moves usually fail with `You can't pick up a liquid directly`. If `look at` an activated sink or fountain shows nothing, move a container into or under the source, then `look at` the container to see the collected substance.

### Using heating and cooling appliances
- If a heating or cooling device is broken or cannot be activated (e.g., `The stove appears broken`), switch to another device such as an oven or freezer.
- After placing the target/substance in a heater, cooler, or other state-change appliance, close or activate it as needed, `wait`, then reopen or remeasure with `look at` or `examine`. Repeat waits until the required state, temperature, or life stage is reached; a single wait is often insufficient. For freezers and ovens, close the door while waiting and open it before inspecting or removing.

### Freezing and freeze/melt verification
- Whenever the task is to freeze a liquid, if a kitchen freezer has not produced an obvious state change after one closed-door `wait`, immediately teleport to the workshop and place the closed container in the `ultra low temperature freezer`. Open that freezer only before inserting or removing; close the door before waiting; open it once to inspect. Do not spend extra steps touring rooms such as the foundry looking for cooling devices.
- For freeze/melt state-change tasks, thermometer evidence is decisive. Once the substance is below 0°C for freezing (or otherwise past the relevant transition), accept that the state change has occurred. Inspect the container once, then `focus on <target substance>` if no renamed substance is visible. Only if observation shows an explicit new name (e.g., `liquid chocolate`) should you focus on that new name. Do not keep waiting for the container text to change to wording like `frozen apple juice`.
- Avoid verification loops after state changes. A closed-door `wait` followed by one `open` and one `look at` or `examine` is enough before re-focusing. If that check does not show the desired state, change the device or move to the ultra-low freezer; do not repeat the same open-check-close cycle more than twice.

### Temperature thresholds and melting point
- For `measure the temperature of X` tasks with bin/color boxes, use the returned thermometer reading as the decision input. Compare the reading exactly against the prompt threshold and branch (`above` vs `below`) to choose the indicated box, then immediately `pick up <target>` and `move <target> to <box>`. Do not re-measure or apply heating/cooling unless the task asks to change the temperature first.
- For threshold-placement tasks, obey any `First focus on... Next focus on...` order first, measure, then branch and move to the correct box. After the move, issue a final `focus on <target>` or the measured substance name before ending.
- For melting-point and threshold tasks, heat or cool the target into the tested region, then use the actual comparison rule in the prompt (e.g., above vs below 50.0°C) as the decision branch. Do not infer a high final temperature equals `above the threshold` without checking the direction and the category boxes; for chocolate melting point, the correct branch is below 50.0°C.

### Moving the changed substance to a named destination
- In tasks that end with moving the changed substance to a named box or container, identify the destination by `look around` in the destination room before moving. Focus on the required object, pick it up, teleport to the destination, use `move <object> to <container>`, then finish with `focus on <object>` if that object is the task's focus target. Do not stop immediately after the move.

### Final focus after the state change
- After melting, freezing, boiling, or otherwise changing a substance, inspect the container contents to learn the resulting substance name, then `focus on <resulting substance>` (e.g., `focus on orange paint`), not on the container or the original ingredients; the task usually requires the result itself rather than the vessel.
- If the task ends with a move or state change and a focus target is named, issue the final `focus on <target>` after that action, then stop. Do not add extra `wait`, `look around`, `examine`, or `focus on` actions after the task condition is satisfied.

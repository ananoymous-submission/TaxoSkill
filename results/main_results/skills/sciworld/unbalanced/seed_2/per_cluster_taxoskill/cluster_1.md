# General guidance

## Environment guidance
- The environment accepts imperative commands, including `look around`, `look at <object>`, `look at inventory`, `objects`, `teleport to <room>`, `pick up <object>`, `focus on <object>`, `examine <object>`, `use <item> on <target>`, `move <object> to <destination>`, `open <object>`, `close <object>`, `wait`, `wait1`, `pour`, `mix`, `dunk <container> in <source>`, `connect ...`, and `disconnect ...`.
- `look around` and `objects` show the current room and visible objects. `look at <container>` shows a container's exact contents, and `look at inventory` shows carried items.
- Use `objects` or `look around` to identify exact descriptors such as `cup containing yellow paint`; prefer those exact descriptors for later unambiguous commands.
- To move between rooms, use `teleport to <room>` followed by `look around`.
- When the task explicitly states where target objects are (`plants are located outside`, `seeds can be found in the bathroom`), go straight to that room and `look around` first. Only fall back to category-likely room search if the named room does not contain them.
- When a required object, instrument, or destination box is not in the current or stated room, search likely rooms one at a time with `teleport to <room>` followed by `look around`. Prefer category-likely rooms: greenhouse for plants, outside for animals, kitchen for instruments/containers, workshop for boxes/electrical parts, bedroom/living room for household items.
- When the environment responds with a numbered list of possible actions, send only the number of the intended option as the next command (for example `0`), not the original action with a number appended.
- If an appended-number command was rejected with `No known action` or `Unknown action`, re-issue the exact command that produced the menu, then send only the number when the menu appears again.

## Execution discipline
- Task completion/stopping: when the task is complete, stop immediately; do not spend additional `step_budget` after the required final state or focus action has been achieved.
- Preserve `step_budget` by avoiding loops, unnecessary repeated failed actions, and extra checks after the required decision or final state is made.
- When a command is rejected or returns `No known action` or `Unknown action`, do not retry the same failed string. Inspect with `look around`, `objects`, `look at <container>`, or `examine <object>` to get the current exact name or descriptor, then issue a corrected command.
- If `focus on <candidate>` or `examine <candidate>` returns `No known action`, abandon that candidate and try another visible object of the requested category rather than repeatedly retrying the failed name.
- Re-inspect an object or container only when its state or contents may have changed. Use `look at <container>` or `look around`/`objects` to confirm the current exact name before relying on it.

# Task-specific guidance

# Measure Temperature and Sort

## Temperature measurement before sorting
- Make the required temperature measurement before moving the target object or substance.
- After reading the temperature, compare the reading to the task's threshold and choose the correct box accordingly.
- When measuring with an instrument, make sure the instrument is in your inventory or current room before `use <instrument> on <object>`. If it is elsewhere, `pick up` the instrument, then teleport back to the target and retry.
- If the substance is inside a container, measure the container contents. After a phase change or other state change the substance name may change; use the updated name shown by the environment for further commands.

## Phase-change measurement
When asked to find a melting point, freezing point, or boiling point:
- Heat or cool the substance in small increments, such as `wait1`. After each increment, first `look at <container>` (or `look around`) to detect a phase change, then use the thermometer for the temperature reading. Do not rely on thermometer readings alone to decide when to stop.
- The target temperature is the reading at or immediately before the first observed phase change, not after prolonged heating once the transition has already happened.
- Compare the measured transition value to any decision threshold from the task, rather than using the temperature reached after the change.

For state-change tasks such as `melt chocolate` or `freeze orange juice`:
- Focus on the substance first, then place it in a container and move that container onto the relevant device.
- Open closed devices before moving objects into them (`open freezer`/`open oven`), activate the device if it is off, then wait and inspect the container contents after each interval.

## Phase-change guardrails
- The first observed phase change is your answer. When a container changes from e.g. `chocolate` to `liquid chocolate` or `water` to `solid water`, immediately use the thermometer on that container and use that reading for decisions. Do not deactivate the device, do not cool/reheat to refine the value, and do not restart the process; doing so causes truncation and regressions.
- After a phase change, continue directly to the final box, focus, or finish action. Do not reverse a transition unless the task explicitly asks for a different final state.
- When freezing, move the container into the freezer and then close the freezer door before waiting. An open freezer door is the most common cause of repeated "still liquid" observations. Wait in blocks (`wait` or several `wait1`s), then open the freezer and inspect `look at freezer` or `look at <container>` before taking temperature readings.
- For the melting point of an initially liquid substance, freeze it solid first. Then remove it from the freezer and warm it at room temperature. Do not put the frozen substance on an already hot stove/oven before you mean to heat it; that overshoots. Use `wait` blocks, then inspect the container after each block. When the name changes to liquid, immediately read the thermometer.

## Phase-change equipment escalation
- For a melting point task starting from a liquid, if a standard freezer leaves the substance liquid after several `wait` blocks and thermometer readings plateau near the freezer low limit (for example mercury stays liquid around -17 degrees), do not keep looping in the same freezer.
- Move the container to an ultra low temperature freezer if one is available (often in the workshop), close its door, then wait and inspect as usual.
- If no colder device is available and the task only compares the melting point to a threshold, use the known or measured melting point of the named substance to make the final box/focus decision instead of waiting indefinitely.

## Conditional placement / finish
- Make the required measurement before moving the target object. Then pick up the object, teleport to the box room, and move the object to the chosen box.
- After moving, verify with `look at <box>`. If the task specifies a final focus, perform that focus last.
- Once the chosen box has been verified and any required final focus is done, stop immediately.

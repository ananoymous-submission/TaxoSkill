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

# Identify Animal by Lifespan

- Enumerate the available animal candidates from the current `look around` or `objects` observation, and use the exact animal descriptors shown for later commands.
- Inspect each candidate with `look at <animal>` or `examine <animal>` to read any available lifespan or description text before deciding.
- Do not select an answer from object names alone unless the environment or well-known science facts clearly support the ranking.
- Distinguish between life stages and whole organisms when the lifespan trait is specified at the organism level; for example, eggs or embryos may not count when the task asks for an animal.
- If no in-game text provides the lifespan comparison, apply standard life-science knowledge for the named organisms rather than guessing from stage labels.
- Identify the animal(s) with the longest and/or shortest lifespan among the available animals, then focus on the requested animal(s) in the requested order.
- Focus on the requested animal itself, not on a pot, cup, cage, or other container holding it.
- If the available animals are life-stage objects, treat the currently visible animal stage objects as the valid focus targets, and focus on the stage object corresponding to the requested animal.
- Re-run `look around` immediately before each focus action, because animals may change stage over time; focus only on the animal currently shown.
- If the requested or later animal/stage is not visible yet, stay in the same room and advance time with `wait1` or `wait`, then `look around` again. Do not roam to other rooms searching for animals that will appear over time.
- When advancing time to reveal an animal or stage, prefer `wait` blocks of 10 steps over many `wait1`s, and re-run `look around` after each block until the required animal appears.
- When multiple animals share the same name, inspect the candidates and resolve the ambiguity by choosing the numeric option matching the target.
- Stop immediately after focusing on the requested animal(s) in the requested order; do not spend extra steps or perform extra checks after the final focus.

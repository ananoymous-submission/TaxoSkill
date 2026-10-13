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

## Grow Fruit by Crosspollination

- First classify the task. This task asks you to grow plants and finally focus on a mature fruit such as `grown cherry` or `grown avocado`, so do not stop and focus on intermediate stages such as `seedling stage`; continue growing until the final requested object appears.
- Pick up several seeds of the required type and plant them in separate pots. Tasks that mention cross-pollination require multiple plants; a single plant will not complete the task no matter how long you wait.
- Ensure each intended pot contains soil before planting. If pots contain only water, go outside, `use shovel on ground`, then `pick up soil`, return to the greenhouse, and move soil into each pot you intend to use. Do not roam through all rooms searching for soil; the outside shovel/ground is the soil source.
- Keep water in the pots. If a pot lacks water, add water from a fountain or sink, or dunk an empty container into a water source and pour it into the pot.
- To collect water from a fixed container such as a fountain, do not try to `pour` the fixed container. Instead, put an empty container into the liquid with `dunk <empty container> in <source>`, then recover the filled container.
- Stay in the greenhouse and advance time with `wait`, re-running `look around` after each wait. Prefer `wait` blocks of 10 steps over many `wait1`s, and re-run `look around` after each block until the requested fruit appears.
- If the target fruit is not visible yet, stay in the greenhouse and advance time with `wait1` or `wait`, then `look around` again. Do not roam to other rooms searching for fruit that will appear over time.
- If a bee hive is present, open the bee hive once plants are mature/flowering to allow cross-pollination.
- When multiple objects share the same name, resolve the ambiguity by selecting the numeric option matching the target after inspecting the candidates if needed.
- Re-run `look around` immediately before the final focus action, because plants may change over time; focus only on the fruit currently shown.
- When the requested fruit appears, focus on the fruit itself, not the pot, cup, or other container holding it. Then stop immediately.

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

## Mixing procedure
- Before `mix`ing, read any recipe or instructions with `look at` or `examine` to identify the required ingredients, then move or pour all of them into a single container first.
- Verify that container contents with `look at <container>` before mixing to avoid mixing an empty or wrong container.
- If no recipe text is present, choose ingredients using standard color-mixing knowledge (for example red and yellow paint make orange) and verify the mixed product with `look at <container>`.

## After `pour`, `mix`, or any chemistry action
- Run `look at <container>` or `look around` to discover the exact name of the newly created substance.
- Inspect `look at inventory` or `look at <container>` after any pour/mix/chemistry action to discover the exact created substance name.
- Focus on the created substance itself, not on the container wording such as `cup containing <product>`. For example, focus on the substance name itself, such as `focus on green paint`, not `focus on wood cup containing green paint`. Focusing on the container does not satisfy tasks that require focusing on the created substance.
- If the environment returns an ambiguous-request menu after a chemistry action, use exact container descriptors to reduce ambiguity rather than retrying the failed wording.

## Liquid ingredients from fixed sources
- To collect liquid from a fixed container such as a toilet or fountain, do not try to `pour` the fixed container. Instead, put an empty container into the liquid with `dunk <empty container> in <source>`, then recover the filled container. This also applies when you need water for plants or state-change tasks.

## Stopping
- After focusing on the requested created product or products, stop immediately.

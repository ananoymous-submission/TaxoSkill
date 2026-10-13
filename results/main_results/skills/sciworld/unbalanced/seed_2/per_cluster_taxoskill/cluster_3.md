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

## Electrical conductivity test

- For any task of the form `if it is electrically conductive, place it in X; if nonconductive, place it in Y`, build exactly one closed series circuit containing the target substance and a bulb/buzzer, then inspect the indicator once.
- Build an explicit series circuit rather than sending bare `connect battery to wire`. Examine each component first, then use exact connection points:
  - `connect battery anode to <wire> terminal 1`
  - `connect <wire> terminal 2 to unknown substance <X> terminal 1`
  - `connect unknown substance <X> terminal 2 to <light bulb> anode`
  - `connect <light bulb> cathode to battery cathode`
- Use a light bulb or electric buzzer as the indicator.
- Do not connect two terminals of the same component directly to each other, and do not try to connect a terminal that is already connected.
- If the indicator is off, classify the target as nonconductive and immediately do the nonconductive final action (move to the nonconductive box, or perform the requested focus/finish). If on, classify as conductive and do the conductive final action.
- Do not rebuild a plain-wire control, do not add/activate a switch, do not swap bulbs/buzzers/wires, and do not re-examine unchanged components after the first valid indicator reading. These extra checks cause truncation.
- If a terminal is already connected and blocks the intended connection, disconnect only that component and reconnect; then still return immediately to the single decision.
- Make the required measurement before moving the target object. Then pick up the object, teleport to the box room, and move the object to the chosen box. After moving, verify with `look at <box>`. If the task specifies a final focus, perform that focus last.
- Stop immediately once the required placement or final focus has been completed.

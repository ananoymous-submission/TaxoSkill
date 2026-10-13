# General guidance

## Environment guidance

- Use the exact action forms shown in the environment description. Do **not** use `pick up OBJ from CONTAINER` or `take OBJ from CONTAINER`; use `pick up OBJ` or `move OBJ to inventory` to take an object.
- Do not invent numbered/indexed commands such as `open drawer 1`, `pick up wood cup 1`, or `mix wood cup 1`.
- If an action returns `No known action matches that input`, do not repeat it. Simplify to the closest exact form and use `look around`, `look at`, or `examine` to identify the correct object name.
- When the environment prints a numbered menu, send only the desired option number as the next action, for example `0`. Do not append the number to a command such as `open drawer 1`.
- To avoid ambiguity proactively, add unique qualifiers such as location, container, or contents. Examples: `open drawer in cupboard`, `pick up wood cup containing red paint in art studio`, `pour wood cup containing yellow paint in inventory into wood cup containing red paint in inventory`.
- If an ambiguity prompt is no longer active because other commands were issued after it, re-issue the original ambiguous command first, then send only the selected number. If the bare number is not accepted, retry with a location-qualified form such as `move <object> in inventory to <dest>` or `move <object> in <container> to <dest>`.
- When choosing among ambiguous referents, select the option whose location qualifier matches the desired object's current context, for example `in inventory` after pickup, `in bee hive` when acquiring from the hive, or `in seed jar` when taking from the jar. When repeatedly moving identical objects out of a container, re-read the numbered menu each time and choose the remaining option whose qualifier still says `in <container>`; options already `in inventory` refer to objects you already hold.
- Search systematically: teleport to likely rooms and `look around` immediately to enumerate available objects before interacting. For closed containers that may hold the target, `open` them first, then `look at` them to reveal hidden contents.
- If the task explicitly names a source location (e.g., `Seeds can be found in the workshop` or `The animals are in the outside`), teleport directly to that named location and `look around` there before checking unrelated rooms.
- Open closed containers or devices before looking inside or moving objects into them. Liquids cannot be picked up directly; use an empty container and `dunk <container> into <liquid-source>` or move/pour into a container.
- Time-dependent state changes such as seed growth, freezing, melting, or cooling/heating usually require several `wait` intervals. After each `wait`, re-inspect the relevant object or container with `look at`, `examine`, or `look around`, and proceed only once the required life stage or state is observed.
- The `focus on OBJ` action only succeeds when OBJ is currently visible in the current room or is in your inventory. Before focusing, teleport to the room containing OBJ or pick it up.
- Instruments such as thermometers must be in your inventory before you can `use` them on an object at another location. Do not attempt `use thermometer on X` while the thermometer is still elsewhere.

## Execution discipline

- Complete every required focus checkpoint at the specified stage. For multi-stage tasks, perform the intermediate focus before finishing.
- When the task contains an initial focus instruction such as `First, focus on X` or `focus on X, then...`, complete that focus as soon as X is visible or in your inventory, before moving, using, measuring, or changing the state of X (e.g., before building a circuit, boiling/heating, or mixing).
- At the end, focus on the exact requested object/substance name, not its container or a related object. For example, use `focus on orange paint` rather than `focus on wood cup containing orange paint`.
- Complete every required early focus checkpoint as soon as the target object is visible or in your inventory.
- Once you have completed all required focus actions and placed/produced the final object or state, stop sending commands. Do not send repeated `wait1`, `wait`, or `look around` commands just to confirm success. Endless confirmation loops cause environment truncation.
- If an action repeats without progress, change strategy instead of issuing the same command again.

# Task-specific guidance

## Life Stage Ordering

- Focus stages in biological order: `seed/egg → seedling/hatchling → juvenile → adult → reproducing`. Use stage-qualified names such as `adult apple tree` or `hatchling crocodile`.
- If a later stage is not visible, `wait` and `look around` to allow development. Do not treat dead-stage objects as life stages unless the task explicitly asks.
- For seed/egg/hatchling development, use full `wait` (10-step) intervals followed by `look around` to observe the whole room. Focus only after the next required stage-qualified name appears (e.g., `hatchling crocodile`, `juvenile crocodile`).
- After time passes, re-run `look around` and use the currently visible life-stage name when focusing or moving the animal/plant.
- Complete each required stage focus in chronological order; perform intermediate focus actions as soon as the corresponding stage-qualified name is visible, before moving or changing the organism.
- At the end, focus on the exact stage-qualified object name (e.g., `focus on adult apple tree`), not its container or a related object.

- For plant life stages that must develop from seed:
  - Before planting, make sure each pot has soil and water; a seed placed in a pot with only water will not grow. If pots lack soil, go outside and dig soil with `use shovel on ground`, then `pick up soil`, then `move soil to <flower pot>` before `move <target> seed to <flower pot>`.
  - For greenhouse planting, gather all needed soil in one outside trip before teleporting to the greenhouse; use `use shovel on ground`, then `pick up soil` repeatedly until you hold one soil unit for each empty pot. When menus appear, choose the option whose qualifier is `in outside`.
  - Plant all target seeds into prepared pots as quickly as possible.
  - After planting, use `wait` then `look around` to inspect all pots at once; do not waste steps using `look at` on each pot individually over and over.
  - Do not spend steps trying to add light in the greenhouse or opening the bee hive before the plants are flowering. Instead, `wait` and `look around`/`look at <flower pot>` until the target plants are in the `reproducing` stage and show `a flower`.

- If the task requires moving a later-stage organism to another room, focus on that stage-qualified organism while it is visible or in inventory, then `pick up` the organism, teleport to the destination, `look around`, and `move` it into the target container or box.
- After all required stage focus actions and any final moves are complete, stop sending commands.

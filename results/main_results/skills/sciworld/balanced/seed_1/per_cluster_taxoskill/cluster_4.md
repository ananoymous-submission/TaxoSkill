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

# Plant Cultivation

## Soil preparation and planting

- Gather all needed soil in one outside trip before teleporting to the greenhouse. Use `use shovel on ground`, then `pick up soil` repeatedly until you hold one soil unit for each empty pot. When menus appear, choose the option whose qualifier is `in outside`.
- When a task requires growing fruit, gather enough target seeds from the stated seed-source room and plant several in separate flower pots at the same time. Do not wait for one plant to reach flowering before planting the next.
- Before planting, make sure each pot has **soil** and water; a seed placed in a pot with only water will not grow. If pots lack soil, go outside and dig soil with `use shovel on ground`, then `pick up soil`, then `move soil to <flower pot>` before `move <target> seed to <flower pot>`.
- Plant all target seeds into prepared pots as quickly as possible.

## Growth and flowering

- For life-stage focus tasks, focus stages in biological order (seed/egg → seedling/hatchling → juvenile → adult → reproducing) and use stage-qualified names such as `adult apple tree` or `hatchling crocodile`. If a later stage is not visible, `wait` and `look around` to allow development, and do not treat dead-stage objects as life stages unless the task explicitly asks.
- For seed/egg/hatchling development, use full `wait` (10-step) intervals followed by `look around` to observe the whole room. Focus only after the next required stage-qualified name appears (e.g., `hatchling crocodile`, `juvenile crocodile`), and reserve short `wait1` checks for temperature/phase transitions near the target state.
- After planting, use `wait` then `look around` to inspect all pots at once. Do not waste steps using `look at` on each pot individually over and over.
- For plant-growth lighting tasks, prefer a naturally lit room before building a custom light circuit.
- Do not spend steps trying to add light in the greenhouse or opening the bee hive before the plants are flowering. Instead, `wait` and `look around`/`look at <flower pot>` until the target plants are in the `reproducing` stage and show `a flower`.

## Cross-pollination and fruit

- Once at least two target plants are flowering, `open bee hive` in the greenhouse to release bees, then `wait` and inspect again. When a `grown <fruit>` or similarly named fruit object appears, `focus on` that exact visible fruit name to finish.
- As soon as at least two target plants are `reproducing` or flowering, immediately `open bee hive`, then `wait` and `look around` for the grown fruit. When the exact fruit name appears, focus on that visible fruit to finish.

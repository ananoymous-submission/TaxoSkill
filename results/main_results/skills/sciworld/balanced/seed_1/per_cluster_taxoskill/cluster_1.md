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

## Temperature measurement procedure

- Locate and pick up the thermometer first. It is commonly found in the kitchen, so if the current or target room does not contain one, teleport to the kitchen and `look around`.
- After obtaining the thermometer, `focus on thermometer`, then focus on the target substance, and only then `use thermometer on <substance>`.
- If the target is a pick-up-able object or material, you may pick it up and measure it from inventory.
- Immediately apply the task's stated threshold or rule to choose the matching destination box or object, then move or focus accordingly instead of exploring further.

## Phase-change / transition-temperature tasks

- For melting-point or boiling-point measurement tasks, heat the substance/container first and `wait` until the phase changes; re-inspect with `look around` or `look at` to learn the updated phase-qualified name (e.g., `liquid gallium`, `water`), then `use thermometer on <new-name>`.
- A thermometer reading before the phase change is only the current temperature, not the transition point, so apply the task threshold only after the phase change is observed.
- For boiling a liquid, first focus on the liquid, then heat it in a container on an activated stove or oven.
- Use short waits such as `wait1` when nearing the phase change, and inspect the container after each short wait. Avoid long `wait` commands that can overshoot the phase change.
- After a heated liquid container becomes empty, treat the liquid as having changed to gas, and stop heating and stop checking further.
- For freezing a liquid, place the filled container into the freezer and keep the freezer door closed for several consecutive `wait` actions before opening it to inspect. Do not open and close the freezer after every single `wait`; repeated opening can prevent the frozen state.
- If the kitchen freezer does not freeze the liquid after several consecutive closed waits, try the ultra low temperature freezer in the workshop: open it, move the filled container inside, close it, and wait with the door closed.

## Moving the measured object or completing the final focus

- If the task requires focusing then moving an object to another room or box, complete the focus while the object is visible or in inventory, then `pick up` the object, teleport to the destination, `look around` to identify the target container or box, and `move` the object into it.
- Stop after the requested focus or placement is complete; do not keep exploring or sending confirmation commands.

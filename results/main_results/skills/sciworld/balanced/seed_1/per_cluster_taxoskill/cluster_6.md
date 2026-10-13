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

# Animal Lifespan Comparison

## Procedure
- Go to the location containing the animals (often `outside`) and `look around` immediately to see all available animals. Do not search rooms for hidden reference notes or books.
- Use common biological knowledge for the observed species to compare life spans, for example: elephants > beavers > chameleons; giant tortoise > rabbit > mouse.
- Choose the longest-lived animal, the shortest-lived animal, or both exactly as the task requests. If more than one animal ties for longest or shortest, include each matching animal.
- Complete the focus actions in the exact requested order. For example, if the task asks to focus on the longest-lived animal then the shortest-lived animal, focus on the longest-lived animal first, then the shortest-lived animal.
- Before each focus, make sure the animal is visible in the current room or in your inventory. If it is not visible, teleport to the animal's location or pick it up, then `look around` and use the current visible exact name.
- Use `focus on <exact visible animal name>`. Do not focus on a container, group label, or related object.
- After time passes or after moving an animal, re-run `look around` and use the currently visible life-stage name when focusing or moving the animal.
- If a focus command fails, re-run `look around` or `look at` the animal to learn the exact current name, then retry with that full name.

## Stop rule
- After all requested focus actions for the longest and/or shortest-lived animal are completed, stop sending commands. Do not send extra `wait1`, `wait`, or `look around` commands to confirm success.

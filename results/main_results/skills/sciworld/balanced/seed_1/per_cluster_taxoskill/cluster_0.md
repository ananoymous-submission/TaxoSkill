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

## Electrical Conductivity Testing

- Read the task text for the exact test object names and the exact result box names (for example a conductor box and a nonconductor/insulator box). Open any closed result box before trying to move an object into it.
- Locate the circuit components: a battery, two wires, one light bulb, and one switch. Use `look around`, `look at`, or `examine` on each component to learn its exact name and terminal names before connecting.
- Batteries, bulbs, and switches normally have `anode` and `cathode` terminals; wires normally have `terminal 1` and `terminal 2`.
- Non-electrical test objects such as fruit may not reveal terminal names through `examine`. They can still be inserted into the circuit with a command such as `connect black wire terminal 2 to <object>`, and the resulting observation will expose the object's terminal names. After that observation, use those exposed terminal names for the remaining connection to the test object.
- Build the series circuit in this order: battery -> wire -> switch -> bulb -> test object -> wire -> battery. Connect terminals, not whole objects, for example `connect battery anode to red wire terminal 1`.
- Include and close/activate the switch before judging the bulb state. An open or missing switch causes a false negative for conductive objects.
- Judge conductivity only after the series circuit is complete and the switch is activated/closed: an on bulb means conductive, an off bulb means nonconductive. Only classify an object as nonconductive after the circuit is fully closed and the bulb is still off.
- If the bulb is off after activating or closing the switch, first re-examine the battery, wires, bulb, switch, and test object to confirm every terminal-to-terminal connection is still connected and the switch is actually on. Then `wait1` and re-examine the bulb before classifying the object as nonconductive. Do not act on a single unverified off reading.
- Metal objects such as paper clips and coins are normally conductive. If a metal test object shows an off bulb after the switch is on and connections are verified, do not immediately classify it as nonconductive. Swap in a different bench bulb, such as the violet or yellow light bulb, and retest. A single off reading can be caused by a bad bulb. Classify the object as nonconductive only after a fully closed circuit with a confirmed working bulb is off.
- Repeat the circuit verification and retest steps for each test object as needed, testing one object at a time.
- After a result is confirmed, place the test object in the matching box, for example `move <object> to <conductive box>` or `move <object> to <nonconductive box>`.
- Once all test objects have been placed in the correct boxes, stop sending commands.



## Additional ScienceWorld container, liquid, device, and recovery notes

- For recipe tasks requiring water, do not rely on an activated sink to produce liquid; if `dunk <container> into sink` reports no liquid, dunk the empty container into a visible liquid source such as `toilet` or `bathtub`, then use that same liquid-holding container as the mixing vessel (`move <solid ingredient> to <container>`, `mix <container>`).
- Time-dependent state changes such as seed growth, freezing, melting, or cooling/heating usually require several `wait` intervals. After each `wait`, re-inspect the relevant object or container with `look at`, `examine`, or `look around`, and proceed only once the required life stage or state is observed.
- If an ambiguity prompt is no longer active because other commands were issued after it, re-issue the original ambiguous command first, then send only the selected number. If the bare number is not accepted, retry with a location-qualified form such as `move <object> in inventory to <dest>` or `move <object> in <container> to <dest>`.
- When choosing among ambiguous referents, select the option whose location qualifier matches the desired object's current context, for example `in inventory` after pickup, `in bee hive` when acquiring from the hive, or `in seed jar` when taking from the jar. When repeatedly moving identical objects out of a container, re-read the numbered menu each time and choose the remaining option whose qualifier still says `in <container>`; options already `in inventory` refer to objects you already hold.
- Search systematically: teleport to likely rooms and `look around` immediately to enumerate available objects before interacting. For closed containers that may hold the target, `open` them first, then `look at` them to reveal hidden contents.

- If the task explicitly names a source location (e.g., `Seeds can be found in the workshop` or `The animals are in the outside`), teleport directly to that named location and `look around` there before checking unrelated rooms.
- Open closed containers or devices before looking inside or moving objects into them. Liquids cannot be picked up directly; use an empty container and `dunk <container> into <liquid-source>` or move/pour into a container. For mixing/crafting recipes, use a clean empty container or clear extra contents first; only the recipe ingredients should be in the container before `mix <container>`.

- After all ingredients are in the mixing container, try the plain container name first, for example `mix glass cup`. If that returns `No known action matches that input`, inspect the container with `look at` or `examine` to learn the updated contents-qualified name, then retry with that full name, such as `mix tin cup containing red paint and yellow paint in inventory`.

- If a heating device is broken or unavailable (e.g., a stove reports it cannot be activated), fall back to another heat source such as the oven. Open the oven before moving the object or container into it, then `activate oven`, `wait`, and re-inspect until the target state change is observed.

## ScienceWorld action syntax and ambiguous-request resolution

- If a `read <full object name>` command fails because the object name includes a leading generic phrase such as `recipe titled`, retry using only the title text (e.g., `read instructions to make peanut butter sandwich`). When reading a titled recipe, prefer `read <title>` directly rather than repeating an overqualified form.
- Use the exact action forms shown in the environment description. Do **not** use `pick up OBJ from CONTAINER` or `take OBJ from CONTAINER`; use `pick up OBJ` or `move OBJ to inventory` to take an object.
- Do not invent numbered/indexed commands such as `open drawer 1`, `pick up wood cup 1`, or `mix wood cup 1`.
- If an action returns `No known action matches that input`, do not repeat it. Simplify to the closest exact form and use `look around`, `look at`, or `examine` to identify the correct object name.
- When the environment prints a numbered menu, send only the desired option number as the next action, for example `0`. Do not append the number to a command such as `open drawer 1`.
- To avoid ambiguity proactively, add unique qualifiers such as location, container, or contents. Examples: `open drawer in cupboard`, `pick up wood cup containing red paint in art studio`, `pour wood cup containing yellow paint in inventory into wood cup containing red paint in inventory`.

## ScienceWorld action prerequisites and focus checkpoints

- For life-stage focus tasks, focus stages in biological order (seed/egg → seedling/hatchling → juvenile → adult → reproducing) and use stage-qualified names such as `adult apple tree` or `hatchling crocodile`. If a later stage is not visible, `wait` and `look around` to allow development, and do not treat dead-stage objects as life stages unless the task explicitly asks.

- For seed/egg/hatchling development, use full `wait` (10-step) intervals followed by `look around` to observe the whole room. Focus only after the next required stage-qualified name appears (e.g., `hatchling crocodile`, `juvenile crocodile`), and reserve short `wait1` checks for temperature/phase transitions near the target state.
- For life-span or relative-trait comparison tasks, use common biological knowledge for the observed species or trait (e.g., elephants > beavers > chameleons; giant tortoise > rabbit > mouse) instead of searching rooms for hidden reference notes or books. After time passes, re-run `look around` and use the currently visible life-stage name when focusing or moving the animal/plant.
- For measurement tasks, locate and pick up the thermometer first; it is commonly found in the kitchen, so if the current or target room does not contain one, teleport to the kitchen and `look around`. Then `focus on thermometer`, then focus on the target substance, and only then `use thermometer on <substance>`. If the target is a pick-up-able object or material, you may pick it up and measure it from inventory. Immediately apply the task's stated threshold or rule to choose the matching destination box or object and move/focus accordingly instead of exploring further.
- For melting-point or boiling-point measurement tasks, heat the substance/container first and `wait` until the phase changes; re-inspect with `look around` or `look at` to learn the updated phase-qualified name (e.g., `liquid gallium`, `water`), then `use thermometer on <new-name>`. A thermometer reading before the phase change is only the current temperature, not the transition point, so apply the task threshold only after the phase change is observed.
- For tasks that require focusing then moving an object to another room, complete the focus while the object is visible or in inventory, then `pick up` the object, teleport to the destination, `look around` to identify the target container or box, and `move` the object into it.
- The `focus on OBJ` action only succeeds when OBJ is currently visible in the current room or is in your inventory. Before focusing, teleport to the room containing OBJ or pick it up.
- Instruments such as thermometers must be in your inventory before you can `use` them on an object at another location. Do not attempt `use thermometer on X` while the thermometer is still elsewhere.
- Complete every required focus checkpoint at the specified stage. For multi-stage tasks, perform the intermediate focus before finishing.

- When the task contains an initial focus instruction such as `First, focus on X` or `focus on X, then...`, complete that focus as soon as X is visible or in your inventory, before moving, using, measuring, or changing the state of X (e.g., before building a circuit, boiling/heating, or mixing).
- At the end, focus on the exact requested object/substance name, not its container or a related object. For example, use `focus on orange paint` rather than `focus on wood cup containing orange paint`.

## Electrical circuit construction and conductivity testing

- Non-electrical test objects such as fruit may not reveal terminal names via `examine`; they can still be inserted into the circuit with commands like `connect black wire terminal 2 to <object>`, and the resulting observation will expose the object's terminal names. Judge conductivity only after completing the series circuit and activating or closing the switch: an off bulb means nonconductive, an on bulb means conductive.
- Before connecting electrical parts, examine each component to learn its terminal names. Batteries, bulbs, and switches usually have `anode` and `cathode`; wires usually have `terminal 1` and `terminal 2`.
- Connect terminals, not whole objects. Example: `connect battery anode to red wire terminal 1`.
- Build a complete series circuit: battery, wires, a light bulb, the test object, and back to the battery.
- Include and close/activate any switch before judging the bulb's state. An open or missing switch causes a false negative for conductive objects.
- Only classify an object as nonconductive after the circuit is fully closed and the bulb is still off.

- If the tested bulb is off after activating or closing the switch, first re-examine the battery, wires, bulb, switch, and test object to confirm every terminal-to-terminal connection is still connected and the switch is actually on. Then `wait1` and re-examine the bulb before classifying the substance as nonconductive. Do not act on a single unverified off reading.
- For plant-growth lighting tasks, prefer a naturally lit room before building a custom light circuit.

## Plant growth and cross-pollination (fruit) tasks

- When a task requires growing fruit, gather enough target seeds from the stated seed-source room and plant several in separate flower pots at the same time. Do not wait for one plant to reach flowering before planting the next.
- Before planting, make sure each pot has **soil** and water; a seed placed in a pot with only water will not grow. If pots lack soil, go outside and dig soil with `use shovel on ground`, then `pick up soil`, then `move soil to <flower pot>` before `move <target> seed to <flower pot>`.
- Do not spend steps trying to add light in the greenhouse or opening the bee hive before the plants are flowering. Instead, `wait` and `look around`/`look at <flower pot>` until the target plants are in the `reproducing` stage and show `a flower`.
- Once at least two target plants are flowering, `open bee hive` in the greenhouse to release bees, then `wait` and inspect again. When a `grown <fruit>` or similarly named fruit object appears, `focus on` that exact visible fruit name to finish.

<!-- SLOW_UPDATE_START -->
## General completion discipline
- Complete every required early focus checkpoint as soon as the target object is visible or in your inventory.
- Once you have completed all required focus actions and placed/produced the final object or state, stop sending commands. Do not send repeated `wait1`, `wait`, or `look around` commands just to confirm success. Endless confirmation loops cause environment truncation.
- If an action repeats without progress, change strategy instead of issuing the same command again.

## Boiling and freezing state changes
- For boiling a liquid, first focus on the liquid, then heat it in a container on an activated stove or oven. Use short waits such as `wait1` when nearing the phase change, and inspect the container after each short wait. Avoid long `wait` commands that can overshoot the phase change.
- After a heated liquid container becomes empty, treat the liquid as having changed to gas, and stop heating and stop checking further.
- For freezing a liquid, place the filled container into the freezer and keep the freezer door closed for several consecutive `wait` actions before opening it to inspect. Do not open and close the freezer after every single `wait`; repeated opening can prevent the frozen state.
- If the kitchen freezer does not freeze the liquid after several consecutive closed waits, try the ultra low temperature freezer in the workshop: open it, move the filled container inside, close it, and wait with the door closed.

## Conductivity testing
- Build the series circuit exactly as: battery -> wire -> switch -> bulb -> test object -> wire -> battery. Verify every terminal-to-terminal connection before judging conductivity.
- Metal objects such as paper clips and coins are normally conductive. If a metal test object shows an off bulb after the switch is on and connections are verified, do not immediately classify it as nonconductive.
- Swap in a different bench bulb, such as the violet or yellow light bulb, and retest. A single off reading can be caused by a bad bulb. Classify the object as nonconductive only after a fully closed circuit with a confirmed working bulb is off.

## Fruit-growing and cross-pollination tasks
- Gather all needed soil in one outside trip before teleporting to the greenhouse. Use `use shovel on ground`, then `pick up soil` repeatedly until you hold one soil unit for each empty pot. When menus appear, choose the option whose qualifier is `in outside`.
- Plant all target seeds into prepared pots as quickly as possible.
- After planting, use `wait` then `look around` to inspect all pots at once. Do not waste steps using `look at` on each pot individually over and over.
- As soon as at least two target plants are `reproducing` or flowering, immediately `open bee hive`, then `wait` and `look around` for the grown fruit. When the exact fruit name appears, focus on that visible fruit to finish.
<!-- SLOW_UPDATE_END -->

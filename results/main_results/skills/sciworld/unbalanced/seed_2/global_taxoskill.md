

## Multi-target life-stage tasks
When the task asks you to focus on the life stages of a plant or animal starting from earliest to latest:
- Enumerate the required stage objects from the current `look around` observation. The named objects are the valid focus targets (for example seed, seedling stage, baby/juvenile/adult stage).
- Focus on each required stage object itself, in the requested order, not on the pot, cup, or other container holding it.
- Re-run `look around` immediately before each focus action, because plants and animals may change stage over time; focus only on the stage currently shown.
- If a later stage is not visible yet, stay in the same room and advance time with `wait1` or `wait`, then `look around` again and focus on the newly appeared stage. Do not roam to other rooms searching for stages that will appear over time.

- When advancing animal or plant growth, prefer `wait` blocks of 10 steps over many `wait1`s, and re-run `look around` after each `wait` block until the next required stage appears.
- When multiple objects share the same name, resolve the ambiguity by selecting the numeric option matching the target after inspecting the candidates if needed.

## Phase-change measurement
When asked to find a melting point, freezing point, or boiling point:
- Heat or cool the substance in small increments, such as `wait1`. After each increment, first `look at <container>` (or `look around`) to detect a phase change, then use the thermometer for the temperature reading. Do not rely on thermometer readings alone to decide when to stop.
- The target temperature is the reading at or immediately before the first observed phase change, not after prolonged heating once the transition has already happened.
- If the substance is inside a container, measure the container contents. After a phase change the substance name may change; use the updated name shown by the environment for further commands.
- Compare the measured transition value to any decision threshold from the task, rather than using the temperature reached after the change.

- For state-change tasks such as `melt chocolate` or `freeze orange juice`, focus on the substance first, then place it in a container and move that container onto the relevant device. Open closed devices before moving objects into them (`open freezer`/`open oven`), activate the device if it is off, then wait and inspect the container contents after each interval.
- When measuring with an instrument, make sure the instrument is in your inventory or current room before `use <instrument> on <object>`. If it is elsewhere, `pick up` the instrument, then teleport back to the target and retry.

- When the task explicitly states where target objects are (`plants are located outside`, `seeds can be found in the bathroom`), go straight to that room and `look around` first. Only fall back to category-likely room search if the named room does not contain them.
- When a required object, instrument, or destination box is not in the current or stated room, search likely rooms one at a time with `teleport to <room>` followed by `look around`. Prefer category-likely rooms: greenhouse for plants, outside for animals, kitchen for instruments/containers, workshop for boxes/electrical parts, bedroom/living room for household items. For `find a(n) <category>` tasks, any visible object of that category can be used; focus on it before moving it. Use `examine <candidate>` to confirm an object's category and exact name before focusing. If a `focus` or `examine` command returns `No known action`, abandon that candidate and try another visible object of the requested category rather than repeatedly retrying the failed name.

## Mixing and creating substances

- Before `mix`ing, read any recipe or instructions to identify the required ingredients, then move or pour all of them into a single container first. Verify that container contents with `look at <container>` before mixing to avoid mixing an empty or wrong container.

- If no recipe text is present, choose ingredients using standard color-mixing knowledge (for example red and yellow paint make orange) and verify the mixed product with `look at <container>`.
After `pour`, `mix`, or any chemistry action:
- Run `look at <container>` or `look around` to discover the exact name of the newly created substance.
- Focus on the created substance itself, not on the container wording such as `cup containing <product>`.
- If the environment returns an ambiguous-request menu after a chemistry action, follow the general `Ambiguous request menus` procedure below and use exact container descriptors to reduce ambiguity.

## Comparative trait questions
For tasks asking you to compare life spans or other organism traits:
- Do not select an answer from object names alone unless the environment or well-known science facts clearly support the ranking.
- Distinguish between life stages and whole organisms when the trait is specified at the organism level (for example eggs or embryos may not count when the task asks for an animal).
- If no in-game text provides the comparison, apply standard life-science knowledge for the named organisms rather than guessing from stage labels.

## Ambiguous request menus
When the environment responds with a numbered list of possible actions:
- Immediately send only the number of the intended option as your next command (for example `0`), not the original action with a number appended (`pick up apple seed 0`).
- If you already sent an appended-number command and received `No known action` or `Unknown action`, re-issue the exact command that produced the menu, then send only the number when the menu appears again.
- Use `objects` or `look around` to identify exact descriptors such as `cup containing yellow paint`; prefer those descriptors for future unambiguous commands.

## Conductivity test termination
For any task of the form `if it is electrically conductive, place it in X; if nonconductive, place it in Y`:
- Build exactly one closed series circuit containing the target substance and a bulb/buzzer, then inspect the indicator once.
- If the indicator is off, classify the target as nonconductive and immediately do the nonconductive final action (move to the nonconductive box, or perform the requested focus/finish). If on, classify as conductive and do the conductive final action.
- Do not rebuild a plain-wire control, do not add/activate a switch, do not swap bulbs/buzzers/wires, and do not re-examine unchanged components after the first valid indicator reading. These extra checks cause truncation.
- If a terminal is already connected and blocks the intended connection, disconnect only that component and reconnect; then still return immediately to the single decision.

## Phase-change equipment escalation
- For a melting point task starting from a liquid, if a standard freezer leaves the substance liquid after several `wait` blocks and thermometer readings plateau near the freezer low limit (for example mercury stays liquid around -17 degrees), do not keep looping in the same freezer.
- Move the container to an ultra low temperature freezer if one is available (often in the workshop), close its door, then wait and inspect as usual.
- If no colder device is available and the task only compares the melting point to a threshold, use the known or measured melting point of the named substance to make the final box/focus decision instead of waiting indefinitely.

<!-- SLOW_UPDATE_START -->
## Phase-change guardrails
- The first observed phase change is your answer. When a container changes from e.g. `chocolate` to `liquid chocolate` or `water` to `solid water`, immediately use the thermometer on that container and use that reading for decisions. Do not deactivate the device, do not cool/reheat to refine the value, and do not restart the process; doing so causes truncation and regressions.
- After a phase change, continue directly to the final box, focus, or finish action. Do not reverse a transition unless the task explicitly asks for a different final state.
- When freezing, move the container into the freezer and then close the freezer door before waiting. An open freezer door is the most common cause of repeated "still liquid" observations. Wait in blocks (`wait` or several `wait1`s), then open the freezer and inspect `look at freezer` or `look at <container>` before taking temperature readings.
- For the melting point of an initially liquid substance, freeze it solid first. Then remove it from the freezer and warm it at room temperature. Do not put the frozen substance on an already hot stove/oven before you mean to heat it; that overshoots. Use `wait` blocks, then inspect the container after each block. When the name changes to liquid, immediately read the thermometer.

## Plant cultivation tasks
- First classify the task. If the task asks you to focus on specific life stages, focus on each required stage in order. If the task asks you to grow a plant and finally focus on a mature product such as `grown cherry` or `grown avocado`, do NOT stop and focus on intermediate stages such as `seedling stage`; continue growing until the final requested object appears.
- In grow-to-fruit tasks, pick up several seeds of the required type and plant them in separate pots. Tasks that mention cross-pollination require multiple plants; a single plant will not complete the task no matter how long you wait.
- Ensure each intended pot contains soil before planting. If pots contain only water, go outside, `use shovel on ground`, then `pick up soil`, return to the greenhouse, and move soil into each pot you intend to use. Do not roam through all rooms searching for soil; the outside shovel/ground is the soil source.
- Keep water in the pots. If a pot lacks water, add water from a fountain or sink, or dunk an empty container into a water source and pour it into the pot.
- Stay in the greenhouse and advance time with `wait`, re-running `look around` after each wait. If a bee hive is present, open the bee hive once plants are mature/flowering to allow cross-pollination.

## Chemistry product focus
- After any pour/mix/chemistry action, inspect `look at inventory` or `look at <container>` to discover the exact created substance name. Then focus on the substance name itself, e.g. `focus on green paint`, not `focus on wood cup containing green paint`. Focusing on the container does not satisfy tasks that require focusing on the created substance.

## Electrical conductivity tests
- Build an explicit series circuit rather than sending bare `connect battery to wire`. Examine each component first, then use exact connection points:
  `connect battery anode to <wire> terminal 1`
  `connect <wire> terminal 2 to unknown substance <X> terminal 1`
  `connect unknown substance <X> terminal 2 to <light bulb> anode`
  `connect <light bulb> cathode to battery cathode`
- Use a light bulb or electric buzzer as the indicator. If the indicator stays off with the substance in the loop, the substance is likely nonconductive; verify by putting a plain wire in the substance's place if needed.
- Do not connect two terminals of the same component directly to each other, and do not try to connect a terminal that is already connected. Disconnect the whole object before reconnecting it in a new circuit.

## Liquid transfer
- To collect liquid from a fixed container such as a toilet or fountain, do not try to `pour` the fixed container. Instead, put an empty container into the liquid with `dunk <empty container> in <source>`, then recover the filled container. This also applies when you need water for plants or state-change tasks.

## Conditional placement / finish tasks
- Make the required measurement before moving the target object. Then pick up the object, teleport to the box room, and move the object to the chosen box. After moving, verify with `look at <box>`. If the task specifies a final focus, perform that focus last.
<!-- SLOW_UPDATE_END -->

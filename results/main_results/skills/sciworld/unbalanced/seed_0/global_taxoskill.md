

## Action Grammar and Disambiguation
- Use only the listed action verbs (`pick up`, `move ... to ...`, `open`, `close`, `look at`, `examine`, `read`, `use ... on ...`, `pour ... into ...`, `mix`, `activate`, `deactivate`, `connect`, `disconnect`, `focus on`, `teleport to`).
- If an action returns `No known action matches that input`, do not repeat it. Rephrase with the allowed grammar: to retrieve an item from a container use `pick up <item>` or `move <item> to <location>`, not `take <item> from <container>`.
- To collect water from a sink: `activate sink`, `move <container> to sink`, then `pick up <container>`.
- On an ambiguous-request prompt with numbered options, issue only the number of the desired option as the next action. When multiple identical objects exist, choose the option whose location text matches where the desired object currently is. For a carried item the desired location is `inventory, in agent, in <current room>`; for an item still inside a container/pot it is `in <container>, in <room>` or `in <pot>, in <room>`.
- Avoid re-issuing the same failed command; switch to a different valid action form or examine the object/container first.

- Before searching broadly, teleport to the room implied by the task or object category and `look around` once: `art studio` for paints, `greenhouse` for plants/seeds/pots/soil, `kitchen` for foods/thermometer/recipe, and the stated destination room for boxes. Only check other rooms or closed containers if the target is not visible there.

- If the target is not visible, check closed containers in the current/implied room by first `open <container>`, then `look at <container>`. A closed fridge/cupboard/closet/paint closet does not reveal its contents to `look around` alone. If `look around` already shows a container's contents (e.g., `a seed jar (containing ...)`), skip `open` and `pick up <target>` directly.
- For "find X / focus on it, then move it to a box" retrieval tasks: once `look around` shows the target, `focus on` it, then `pick up <target>` before teleporting to the destination. At the destination, `look around` once to locate the requested box, then `move <target> to <box>`; do not teleport away while the target is still on the ground.
- If `focus on <object> <descriptor>` fails with `No known action matches that input`, retry with the shortest base object name (for example `focus on apple tree`) and then select the numbered option whose location text matches the desired object.

## Substance Creation and Final Focus

- If `read <recipe titled ...>` fails with `No known action matches that input`, retry with a shorter phrase: `read recipe` when only one recipe is visible, or `read <title without 'recipe titled'>` (e.g., `read instructions to make salt water`). Do not re-issue the full `recipe titled ...` command.
- Transfer solid or powder ingredients into the mixing container with `move <ingredient> to <container>`, not `pour`. If a `pour <solid> into <container>` attempt fails with `... is not movable`, switch immediately to `move <ingredient> to <container>`.
- If no empty mixing container is visible near the recipe/ingredients, teleport to the kitchen, `look around`, and use an empty glass cup or bowl as the mixing container.
- Read any recipe with `read <recipe>`, open closed ingredient containers before pouring or mixing, and combine ingredients in a container.
- After a chemical reaction produces a named substance inside a container, complete the task by focusing on the resulting substance name given in the task, not on the container (unless the task explicitly names the container).
- Verify with `look at <container>` that the expected substance is present before focusing on it.

## Electrical Conductivity Testing
- First `examine` the battery, wires, bulb, and test object to learn their terminals (`anode`/`cathode` or `terminal 1`/`terminal 2`).
- Build one closed series loop: battery anode -> wire1 -> test object -> wire2 -> bulb anode -> bulb cathode -> battery cathode.
  Example commands:
  - `connect battery anode to <wire1> terminal 1`
  - `connect <wire1> terminal 2 to <object> terminal 1`
  - `connect <object> terminal 2 to <wire2> terminal 1`
  - `connect <wire2> terminal 2 to <bulb> anode`
  - `connect <bulb> cathode to battery cathode`
- `examine <bulb>`. A lit bulb means conductive. An off bulb is evidence of nonconductivity only after the loop is verified: disconnect the test object and connect the two free wire terminals that went to the object directly to each other, then `examine <bulb>`. If the bulb is still off with the object shorted, fix the circuit before classifying. If the bulb lights only when the object is shorted, the test object is nonconductive and can be placed in the nonconductive box.
- If `examine <test object>` does not show terminal info, do not repeat the same examination; proceed to connect wires to `<object> terminal 1` and `<object> terminal 2`.
- If a connection fails because a terminal is already connected, `disconnect <component>` at the object level before reconnecting.

- Build the conductivity loop once and `examine <bulb>` once. If it is off, short the test object and `examine <bulb>` once. Inspect component connections only once after that; if the intended series loop is intact, do not keep rebuilding the same circuit.
- If a switch is available, include it in series and `activate switch` once. If the bulb is still dark, try at most one alternate bulb or wire. Then stop diagnosis and proceed to the final classification/placement instead of spending further actions re-examining the same off bulb or endlessly rewiring.
- Do not re-`examine` the same bulb/component repeatedly when it keeps returning the same off/unlit state; that state is not progress.

## Thermal / Melting-Point Tasks
- Distinguish between current temperature and melting point. A hot liquid is not evidence that its melting point is high.
- If the task only asks whether a melting point is above or below a threshold, do not chase the exact melting point through repeated heating/cooling cycles.
- First observe the sample's current phase and temperature; if its phase already implies the answer (for example a substance that is liquid at a temperature well below the threshold must have a melting point below that observed temperature), decide immediately.
- Otherwise bring the sample near the threshold using a heating/cooling device, monitor with the thermometer, and `examine` the sample's phase: solid at the threshold means the melting point is above it; liquid at the threshold means the melting point is below it.
- Prefer active devices (stove, oven, freezer) over passive waiting to change temperature quickly.

- If `examine <substance>` or `look at <container>` returns only the name and does not state solid/liquid/gas, do not keep re-checking. Classify once from the measured temperature at the threshold plus broad melting-point knowledge, then issue the final box focus.

- Use `wait1` (one iteration) while heating or cooling, then check temperature and phase after each step. Avoid `wait` (10 iterations) on an active hot stove/oven; it overshoots the threshold, can set the sample on fire, and makes it hard to cool back down.
- Before heating or cooling, put the substance in a movable container such as a cup, bowl, or pot. If it melts, move the container rather than trying to pick up or pour the liquid. If liquid is stuck on a hot appliance, do not repeat failed `pour` attempts; deactivate the appliance and move the container/cool it as soon as possible.
- Stop heating as soon as the sample is near or just beyond the requested threshold; check phase at that temperature and answer above/below.

- For simple temperature-measurement/box-sorting tasks, first obtain and carry the thermometer. Teleport to the kitchen, `look around`, `pick up thermometer` (even if it is already visible or `focus on thermometer` succeeds), then `focus on thermometer`. Keep the thermometer in inventory before teleporting to the target; `use thermometer on <target>` only works with a carried thermometer. Then go to the target, `focus on <target>` if required, and `use thermometer on <target>`. Only after the measurement `pick up <target>` and `move <target> to <color box>` in the stated destination room.

## Plant Growth and Pollination
- For grow-a-plant tasks: focus on a seed if asked, then `move <seed> to <pot>` that contains soil. If available pots contain only water, first obtain soil/dirt from the ground outside using a shovel/examine and move it into the pot before planting.
- Keep the pot watered, then `wait` and `look at <pot>` to track stages: seed -> seedling -> adult -> reproducing.
- For cross-pollination/fruit tasks: when plants are in the reproducing stage and show flowers, manually `pick up pollen` from one flower, choose the inventory pollen option, then `move pollen to flower` on a different plant. After transfer, `wait` and `look at <pot>` for the grown fruit/named object before focusing on it.

## State-Change (Freeze/Melt) Tasks
- For freeze tasks, after focusing on the substance, put it in a freezer: `open freezer`, `move <substance> to freezer`, then `wait` and `examine <substance>` until solid.
- For melt-then-freeze tasks, melt first in an oven/stove only until the substance becomes liquid; do not leave it heating to the point of fire. If it catches fire, remove it from the hot appliance and deactivate the appliance before cooling it.
- Monitor progress with `use thermometer on <substance>`; once the desired phase is reached, move the container/substance to the next appliance or focus as required.

- In freeze/melt tasks, after moving the substance into the appliance and waiting once, confirm with `use thermometer on <substance>`. If the measurement indicates the target phase/temperature has been reached, do not loop further `examine`/`focus` commands; issue the task's required final `focus on` once and stop.

## Life Science and General Completion
- For 'longest life span' or similar comparisons, rely on broad biological knowledge of animal class and typical lifespan, not object size or current life stage. Tortoises and parrots can outlive small mammals; small mammals usually outlive insects; an egg/baby carries the adult species identity. Do not search every room or book unless the task explicitly asks for written facts; examining animals usually only shows their current stage.
- For 'shortest life span' comparisons, use the same broad-knowledge shortcut: small short-lived mammals (e.g., mouse, hedgehog) are shorter-lived than rabbits, wolves, and tortoises. Focus directly on the chosen animal and stop; do not examine each candidate.
- For life-stage ordering tasks, use `look around` to see the organism's current stage (e.g., baby/juvenile/adult). Focus on the required stages in the observed order. Use `wait` only to advance development when needed, then re-check `look around`; avoid repeated `examine` of the same animal.
- When a numbered choice yields a specific generated item name (e.g., `bee 2`), use that exact name for the next commands instead of the generic category name. If that name is unknown, `look at inventory` or `look around` to get the current object name.
- Stop after moving the required object to the required box/container; do not wait, re-check it, or replace it. Post-task state changes such as a plant becoming 'unwell' do not mean the task needs redoing unless the task explicitly requires keeping it alive.

## Hard Stop After Final Action
- Once you have issued the task-final action (final `focus on`, final box placement, final pollination, or other required completion signal), take no further actions. Do not call `wait`, `wait1`, `examine`, `look at`, `use thermometer`, or repeat the same final action.
- Repeating a completed final action or waiting after it wastes steps and causes truncation. If the current observation already confirms success, stop immediately.

<!-- SLOW_UPDATE_START -->
Hard stop after the final required action.
- After the observation confirms the final required action has succeeded (for example `move X to Y`, `focus on X`, or final box placement), emit no more actions. Do not call `wait`, `wait1`, `look around`, `look at`, `examine`, `use thermometer`, or repeat the final command.
- Never express stopping by issuing `wait1`. If your reasoning says the task is complete, stop immediately with no action.
- For find/focus/move retrieval tasks, once `move <target> to <box>` returns success, the task is finished. Do not re-move, re-check, or wait.

Retrieval and ambiguous animals.
- For generic find-an-animal tasks, prefer a visible singular animal in an open area. If no animal is visible, go directly to outside and look around before opening hives or searching bedrooms. Do not open a beehive unless the task requires bees or pollen; ambiguous identical bees waste steps.

Electrical conductivity.
- Build one initial loop only. If a switch is available, include it in series from the start and activate it once before the first bulb exam. Do not add a switch later.
- Examine each component once. If `examine <test object>` gives no terminal or material info, do not repeat it; connect to `<object> terminal 1` and `<object> terminal 2`.
- Do not put the test object into inventory during diagnosis. After the diagnosis budget is spent, pick it up only for immediate final placement, or issue `move <test object> to <box>` directly.
- After building, `examine <bulb>` once.
- If lit: place the object in the conductive box and stop.
- If off: verify with exactly one short: `disconnect <test object>` only, connect the same two wire terminals directly to each other, and `examine <bulb>` once. If the bulb now lights, place the object in the nonconductive box and stop.
- If the shorted circuit is still off: inspect the series connections only once, repair at most one obvious open, and try at most one alternate component total, either one bulb or one wire. Do not try a bulb and then a wire, do not try every color, and do not rebuild or re-short the same circuit again.
- After that budget is spent, stop circuit work permanently. Use `look at <test object>` once to identify its material. Metal objects are conductive; wood, plastic, ceramic, rubber, glass, food, and fabric are nonconductive. If the material is still unknown, make a single best box placement from any clue you have and stop. Re-examining the same off bulb is never progress.

State-change and phase tasks.
- For heating or cooling state changes, the final required action is normally one `focus on` for the task-named substance or generated phase name. Issue it once as soon as the phase has changed and stop.
- For boil or evaporate tasks: once the thermometer reads above boiling point, stop checking the liquid. Focus on the gas phase name once if one appears; otherwise focus on the original substance once and stop.
- For freeze or melt tasks: after moving into the appliance and waiting once, confirm with `use thermometer` once. If the target phase is reached, issue the required final `focus on` once and stop.

Water collection.
- If a sink is broken, try another room's sink first. `activate sink`, `move <empty container> to sink`, then `pick up <container>`. For a bathtub, activate it, close the drain, wait until water appears, move a container into it, then pick it up.

Paint, color, and simple mixtures.
- In paint or color tasks, use an empty destination container in the art studio. Pour each named source liquid into that empty container, then `mix <container>`. Do not pick up full source cups or pour unlabeled wood cups into each other.
- For numbered options, select the destination container you are holding or just moved, and the source whose location contains the named substance.

Melting-point threshold.
- Keep the sample in a movable container. Use only `wait1` on an active appliance; after each `wait1` check `use thermometer` and `examine <substance>` once each.
- Stop heating and deactivate the appliance as soon as the transition brackets the threshold. Move the container off the hot appliance immediately.
- Classify with one clean phase observation at the threshold: liquid at the threshold means below; solid at the threshold means above. Then focus on the corresponding box once and stop. Never leave a melted sample on a hot stove or oven.

Plant growth and pollination.
- Prepare soil in all pots before planting any seeds. Plant all seeds, water, then wait and inspect all pots each cycle until the required stage.
- For cross-pollination, wait until all required plants are in the reproducing or flowering stage before moving pollen.
<!-- SLOW_UPDATE_END -->

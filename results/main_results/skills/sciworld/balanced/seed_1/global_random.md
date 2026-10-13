

## ScienceWorld Action Grammar and Disambiguation
- Use only the exact verbs from the available-action list, e.g. `pick up` rather than `take` or `remove`, and `move OBJ to OBJ` rather than `put`.
- When the environment responds with `Ambiguous request: Please enter the number for the action you intended (or blank to cancel):`, your next action should be exactly the number of the intended referent, such as `0` or `1`. Do not repeat a modified command like `pick up orange seed 0`.
- Use the candidate locations shown in the ambiguous list, such as inventory vs. container vs. room, to select the correct referent.

## Navigation and orientation
- When starting a task or entering a new room, teleport to the most likely room (e.g. greenhouse for plants, kitchen for seeds/ice/boxes, outside for animals) and use `look around` immediately to list available objects.
- If the target item or container is not in the current room, teleport to its likely room and `look around` rather than guessing; do not repeat the same room scan.
- If the target item is still not visible after `look around`, open and inspect closed containers or devices in the current room (`open fridge`, `look at fridge`; `open freezer`, `look at freezer`; `open large cupboard`, `look at large cupboard`; `open oven`, `look at oven`) before leaving; many task objects and substances start hidden inside closed containers.

## Multi-Stage Focus Tasks
- When a task requires focusing on several objects, life stages, or intermediate products in order, continue issuing `focus on <named target>` for every required target. Do not stop after the first or intermediate focus.
- Focus on the exact named substance, plant stage, or product that the task asks for, not its container or vessel (e.g. `focus on green paint`, never `focus on glass cup`). Continue focusing through every required intermediate and final target, and use the same task wording when possible.

## Find-and-move tasks

- For conditional placement tasks based on a measurement or property (e.g. above/below a temperature, conductive/nonconductive), determine that property before teleporting to the destination boxes. If an instrument is required, focus on the instrument and substance in the requested order, pick up the instrument so it is available, then `use <instrument> on <substance>` before deciding which box to move the target to.
- For find X, focus on it, move it to Y box in room Z tasks: locate X, `focus on X`, `pick up X`, teleport to room Z, `look around` to locate the target box, then `move X to <box>`.
- Move objects into containers with `move OBJ to CONTAINER`; containers are usually open, but devices such as ovens or freezers may need `open` before moving objects into them.

## Ambiguous requests and identical containers
- A numeric choice is valid only as the immediate next action after an `Ambiguous request:` prompt. After the action executes, do not reuse a previous option number; if you need to inspect another candidate, reissue a normal command (e.g. `look at wood cup`) to get a fresh menu.
- When several identical objects/cups exist, use the location shown in the candidates (`in inventory` vs. `in <container>` vs. `in <room>`) and inspect contents with `look at`/`examine` before pouring, mixing, or focusing on one.
- If a raw number reply returns `No known action matches that input`, you are outside an ambiguity context; issue a normal command instead.

## Chemistry, recipes, and measurement

- To collect a liquid from a fixed container such as a sink, bathtub, or toilet, do not `pick up` or `pour` the liquid directly. If the sink is empty, `activate sink` and close the drain first; then `dunk <empty container> into <liquid source>` and `pick up` the container holding the liquid.
- For mix/create recipes, use a clean, empty container. Do not mix in a container that already has other items, because `pour` will carry those contaminants and prevent the desired product.
- Move or pour only the specific required ingredient (e.g. the cup containing blue paint); avoid pouring a contaminated container's entire contents into the working container. If contamination occurred, start a clean container with only the required materials.
- For melting/boiling point tasks, the relevant value is the temperature at which the substance changes state, not an arbitrary overheated or burning sample's current temperature; keep heating gradual and use the thermometer reading around the phase change (or the known material property) for any above/below decision.

## Plant growth and cross-pollination
- Plant multiple seeds early in separate pots so the required plants mature in parallel; ensure each pot has both soil and water. Gather soil by `use shovel on ground`, then `pick up soil`; add `move soil to flower pot N` before planting `move <seed> to flower pot N`.
- Wait and look around until at least two plants show flowers or a reproducing stage.
- Then cross-pollinate immediately: `open bee hive`, but do NOT `use adult bee on flower` or `use adult bee on flower pot`; that is not a valid bee action. Instead use `move <adult bee> to <flower>` to place an adult bee onto a flower, and repeat for another flower/pot so pollen moves between different flowers. Wait for fruit, then focus on the final named fruit (e.g. `focus on apple` or `focus on grown apple`).

## Life stages and waiting
- For grow/plant and animal life-stage tasks, after planting seeds or locating eggs/babies, use `wait` and then `look around` repeatedly; immature objects change into later stages over time (e.g. a crocodile egg becomes a hatchling, juvenile, then adult; planted seeds become reproducing plants). Do not try to focus on a stage before the corresponding object exists.
- When the task asks for multiple ordered stages, `look around` between each focus to see the next stage, then focus on the exact stage object currently present for the target species.
- Once the required target has been focused successfully, do not keep issuing `wait1` actions; stop or move on to the next required target.

## Repeated identical items and long ambiguity lists
- When pulling several identical items from the same container (e.g. seeds from a seed jar), choose the candidate whose location is still `in <source container>` on the fresh menu, not one already `in inventory`; this avoids picking the same item twice. If an old option number fails, reissue the normal command to get a fresh menu.
- In long ambiguous `pick up`, `pour`, or `mix` menus involving identical containers (e.g. wood cups of different paint colors), never assume a previous menu order is still current. For paint/color recipes, do not carry every identical cup in inventory: keep the target cup on the table or use a distinctly named clean container (`jug`, `glass cup`, `ceramic cup`) as the mixing target, so location labels separate source and target. Select only the source whose contents you just confirmed, pour one ingredient at a time into that target, then `mix` immediately. If `mix` reports `There is only one thing`, pour the missing ingredient into that target and mix again. Re-inspect candidates only after a command has actually moved or changed items.

## Electrical conductivity tasks
- Build only one minimal loop on the table, then stop inspecting. Connect: `connect <wire A> terminal 1 to battery anode`, `connect <wire A> terminal 2 to <target> terminal 1`, `connect <wire B> terminal 1 to <target> terminal 2`, `connect <wire B> terminal 2 to <bulb> anode`, `connect <bulb> cathode to battery cathode`. Batteries and bulbs use `anode`/`cathode`; wires and targets use `terminal 1`/`terminal 2`. Unknown substances show no extra detail on `examine`, so do not re-examine them.
- Check the bulb once. If it is on, the target is conductive; move it to the conductive box.
- If it is off, run exactly one control: `disconnect <target>` only, leaving the wires, bulb, and battery connected. Connect the two wire terminals that had gone to the target directly together and check the bulb once. If the control bulb lights, the target is nonconductive; move it to the nonconductive box.
- If a switch-free control loop is still off, stop after that one attempt. Do not disconnect/rebuild the circuit, swap bulbs or wires, toggle switches, `activate battery`, or keep re-examining connections. Use known material properties: metal objects such as pots and forks are conductive; unknown substance targets whose target loop stayed off are usually nonconductive. Move the target to that box and finish.

## Phase-change completion must be state-explicit
- For freeze/melt tasks, inspect the substance itself (`examine <substance>`), not only its container, and look for the required state adjective: `solid <substance>` for freezing, `liquid <substance>` for melting. The task is not done until that adjective is observed.
- If a melt target is not already `solid X`/`frozen X`, freeze it first in a closed, activated freezer until `examine X` shows `solid X`; only then heat it, and deactivate immediately when `examine X` shows `liquid X`.
- Do not declare success from a high thermometer reading alone. If `examine X` shows `gaseous X`, deactivate the appliance immediately and cool/condense; restart from a fresh sample if available.
- For freezing, if the first check is not `solid X`, close the freezer and wait at least three full `wait` actions before the next check; opening too frequently prevents freezing.

## Life-span comparison vs. egg-dismissal
- For 'longest life span' / 'compare life span' tasks, compare the species implied by every visible candidate, including eggs. Eggs are evidence of a species; do not automatically choose a hatched baby if a longer-lived species appears only as an egg.
- Use compact lifespan order when the choices are ambiguous: parrots/tortoises > hedgehogs/rabbits > chipmunks/frogs/lizards. Example: among `chameleon egg`, `baby chipmunk`, and `parrot egg`, focus on `parrot egg`.

<!-- SLOW_UPDATE_START -->
## Electrical conductivity: simple, bounded tests
- Build only this loop: battery anode -> wire A terminal 1; wire A terminal 2 -> target terminal 1; target terminal 2 -> wire B terminal 1; wire B terminal 2 -> bulb anode; bulb cathode -> battery cathode. Use only one battery, one bulb/buzzer, two wires, and the target. Do not add a switch unless the task explicitly names or requires one.
- Leave unused components on the table. Do not examine the target repeatedly; unknown substances show no extra detail. Batteries and bulbs use anode/cathode; wires and targets use terminal 1/terminal 2.
- If the bulb is on with the target connected, the target is conductive; move it to the conductive box immediately.
- If it is off, perform exactly one control test: `disconnect <target>` and connect the two wire ends that had gone to the target directly together. If the control bulb lights, the target is nonconductive; move it to the nonconductive box immediately.
- If a switch-free control loop is still off, stop diagnosing. Use known material properties: metal objects such as metal pots and metal forks are conductive; unknown-substance targets whose target loop stayed off are nonconductive. Place the object and finish.

## Phase change: freeze/melt
- Freezing: place the closed liquid container in the freezer, close the door, and confirm the freezer is activated. Wait 3 full `wait` actions before the first check, keeping the door closed. Check with `examine <substance>`; completion requires seeing `solid <substance>`.
- Melting: heat a frozen/solid sample gradually. Deactivate the appliance as soon as `examine <substance>` shows `liquid <substance>`. Do not keep heating until it becomes `gaseous <substance>`. If gas forms, deactivate immediately and cool/condense or restart from a fresh sample.
- Never declare phase-change completion from a thermometer reading alone; require the exact state adjective from examining the substance itself.

## Plant/cross-pollination: minimum-step execution
- For grow-fruit tasks, plant exactly two pots. Gather exactly two seeds and two piles of soil; do not collect extra supplies or prepare extra pots.
- Put soil and water in each pot, then move one seed into each pot. Start waiting immediately after the second seed is planted.
- Alternate `wait` with `look around`. Stop waiting as soon as any two pots show flowers or a reproducing stage, even if other pots are not ready.
- Pollinate with the fewest actions: `open bee hive`, then `move adult bee to flower` (not `use adult bee on flower`). On the ambiguous menu choose a bee whose source is `in bee hive`. Then move a second bee to a different flower/pot.
- After pollination, wait and `look around` for fruit. The moment fruit exists, issue `focus on <task-fruit-word>` (e.g. `focus on apple`, not `focus on red apple`). If the focus menu is ambiguous, immediately enter `0`; any listed fruit satisfies completion.

## Animal life-span tasks: direction matters
- LONGEST life span: treat eggs as evidence of the species they represent and use this order: parrots/tortoises > hedgehogs/rabbits > chipmunks/frogs/lizards. Example: focus on `parrot egg` over `baby chipmunk`, `chameleon egg`, or `baby beaver`.
- SHORTEST life span: ignore eggs when any hatched animal is visible. Choose the shortest-lived visible hatched animal using the same order: chipmunks/frogs/lizards are shorter-lived than hedgehogs/rabbits, which are shorter-lived than parrots/tortoises. Example: with `frog egg`, `giant tortoise egg`, and `baby hedgehog`, focus on `baby hedgehog`.
- If a shortest-life-span task has no hatched animal visible, only then compare eggs and choose the shortest-lived species egg.
- Do not leave the location to search for life-span books unless the task explicitly tells you to; compare the actual candidates present.
<!-- SLOW_UPDATE_END -->

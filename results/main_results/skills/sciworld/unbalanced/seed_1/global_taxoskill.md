

## Ambiguous Requests
ScienceWorld may respond to a command with `Ambiguous request: Please enter the number for the action you intended (or blank to cancel):` followed by numbered choices.
- Your next command should be **only** the number of the intended choice, e.g. `0` or `10`.
- Do **not** append the number to the original command (e.g. `open drawer 0` or `pick up avocado seed 0`) and do **not** repeat the action verb or add location details.
- Resolve the ambiguity immediately before issuing any next action.
- When choosing among alternatives, select the one matching the intended source/destination location, such as `(in inventory, in agent, ...)` when you mean the container you are carrying.
- If the same ambiguous prompt appears again, reply with the bare number that matches the intended referent.

- If an action fails with `No known action matches that input`, retry with an alternate referent from the observation: for recipes use a natural title/object name (`read instructions to make banana sandwich` or `read recipe`), not `read recipe titled ...`; for described objects use the base noun (`focus on pillow`, not `focus on white pillow`). Do not repeat the failing phrasing.

## Object Handling Before Use, Movement, and Final Placement

- For time-dependent processes not covered by the plant-growth or freezing sections, such as animal life-stage or melting-point tasks, stay in the same room after initiating the change; alternate `wait`/`wait1` with `examine`/`look at` the target, or `use thermometer on <substance>` after each wait, and repeat until the desired state/stage is observed. Do not wander while the process is running.
- When heating a solid to find a melting point, measure after each wait; if the original name fails or becomes ambiguous after a phase change, retry with the new state name (e.g. `use thermometer on liquid tin`) and select the referent inside the heating container.
- Use `pick up`, not `take`, to carry solid tools and target objects; do not try to `pick up` liquids (see Liquid and Substance Handling).
- Before using a tool on a target, have the tool available in inventory and be in the same room as the target; if needed, `pick up` the tool first (e.g. `pick up thermometer`, then `use thermometer on unknown substance B`).
- When moving between rooms, carry required tools and target objects in inventory.

- To change an object's state with a device, activate the device first and open its door if it has one, then move the object inside (e.g. `activate stove`; `open oven`; `move chocolate to oven`). If the device is broken or cannot be activated, try an alternate heat/cool source such as the oven or freezer.
- For final placement, first `pick up` the target, `teleport to` the destination room, `look around` to locate the named box/container, then `move <target> to <container>`.
- If an object is inside a closed container, `open <container>` and then `look at` or `examine` it to inspect the contents.

- To collect a liquid into an empty container, `move <empty container> to <liquid container>` (e.g. `move glass cup to sink`) so it fills, then `pick up` the container. Do not `pick up` the liquid directly or try to `pour` from a fixed source.
- To create a mixture/substance by mixing, move all required ingredients into a single **empty** container (e.g. `move bread to glass cup`, `move banana to glass cup`), then run `mix <container>`. Do not run `mix <ingredient>`; first `examine` the container and remove any pre-existing contents so only the required ingredients are present. If `mix <container>` reports no reaction or the container is empty, verify with `examine <container>` and use a clean/empty container containing only the recipe ingredients.

## Focus and Milestone Protocol

- If `focus on <target>` fails with `No known action matches that input`, the target may be in another room or inside a closed container; locate/open it first, then retry the same `focus on` command.
- For find-a-living/non-living thing tasks, choose any visible object that fits the category, `focus on` it, `pick up` the target, teleport to the destination room, locate the named box with `look around`, then `move` the target to that box.
- Many tasks ask you to "focus on X" multiple times, e.g. "First, focus on X. Next, focus on Y." Execute a separate `focus on` command for **each** named target, in the exact order given.
- Do not stop after focusing on only the first target. Continue until all required focus actions have been performed.
- For ordering/life-stage tasks ("focus on the N life stages ... from earliest to latest"), each stage is its own focus target: focus on the earliest visible stage, then the next, and so on.
- If the task says to focus on an intermediate product part-way through, call `focus on <intermediate>` immediately after that intermediate is created or observed, before continuing further mixing or transformations.
- When a multi-step task has a final answer object, ensure you finish by focusing on that answer object after the prerequisite actions.
- Do not skip focus calls while resolving ambiguity; finish the disambiguation by answering with the number, then issue the focus command.

- For temperature or melting-point tasks, after focusing on the thermometer and the substance, call `use thermometer on <substance>`. Compare the reported degrees celsius with the task threshold, then `focus on` or `move` the selected box/object.

- If the task asks for the **temperature** of a substance (e.g. `unknown substance B`) rather than a melting/freezing point, measure it in place with `use thermometer on <substance>`; do not heat, freeze, or wait first. For melting-point tasks, only heat/cool a solid substance until liquid appears; if the target is already liquid (e.g. `orange juice`, `mercury`), a direct measurement is usually enough for the threshold comparison.

## Navigation and Likely Tool Locations
- Start by teleporting to the room named in the task, then `look around` to locate the target object/substance and nearby containers/devices.
- If a needed tool is not present, search likely rooms: the kitchen often has a thermometer, fridge, and freezer; the workshop often has batteries, wires, bulbs, and boxes.

## Mixing and Pouring Liquids/Paints
- When the goal is a mixed liquid or paint, pour the **contents** of each source container into one empty container (`pour <source cup> into <empty container>`), then `mix <container>`. Do not move whole source cups into the target container; nested cups will not mix.
- Before choosing an ambiguous source cup by number, inspect candidate containers with `look at <container>` or `examine <container>` so you select the cup holding the required color/substance, not merely the first option.
- After each pour, `examine <target container>` to confirm what is now in the mixture before adding the next ingredient or running `mix`.

## Electrical Conductivity Testing
- To test conductivity, build a closed circuit with a battery, wires, a bulb, and the unknown substance: use specific terminals (`connect battery anode to <wire> terminal 1`), chain through the substance to the bulb, and return to the battery cathode. If a switch is available, include it and `activate`/close it before judging the bulb.
- After wiring, `examine <bulb>` to verify the bulb state and trace every connection. Treat an off bulb as evidence of nonconductivity only after confirming the circuit is actually closed and powered.
- Decide conductive/nonconductive before moving the substance to the answer box; picking it up disconnects it from the test circuit.

## State-Change Monitoring and Early Termination
- For freezing, melting, heating/cooling, and animal/plant life-stage tasks, after starting the process or placing the target in the device, stay in the same room. Alternate `wait`/`wait1` with direct state checks: use `use thermometer on <substance>` after each wait for freeze/melt/heat tasks; use `examine <target>` or `look at <container>` after each wait for stage changes.
- After each check, update the referent if the object's name or state has changed (e.g. `liquid lead`, `frozen chocolate`); do not keep checking only the old solid/liquid name.
- For threshold/comparison tasks (e.g. `if melting point is above/below X`), decide as soon as a measurement or known property establishes the comparison. Do not wait for a full phase transition unless the task explicitly requires observing that transition.
- If repeated checks show no change, verify the device is activated and the target is actually inside the active/closed device, then continue waiting and checking.

## Animal Life-Stage and Lifespan Tasks

- If the animal/egg or life-stage target is not visible in your current room, check `outside` early (`teleport to outside` then `look around`) before roaming through all indoor rooms. ScienceWorld commonly places animal eggs and adults outdoors, so this saves steps.
- For tasks requiring focus on several life stages from earliest to latest, if only one stage is visible, stay in the same location and use `wait`/`wait1` plus `examine`/`look at` to observe the organism change into later stages. Do not roam through every room searching for stages.
- For `shortest/longest life span` tasks, compare the visible animal objects themselves, not eggs or offspring, unless the task explicitly asks for an egg or juvenile stage. If only one non-egg animal object is visible, it is usually the intended animal to focus on.

<!-- SLOW_UPDATE_START -->
These rules override any conflicting guidance in the sections above.

## Lifespan comparisons
When a task asks for longest or shortest life span, choose by species' known adult lifespan, not by whether the visible object is labeled egg, baby, juvenile, or adult. A crocodile egg is the crocodile species and is a valid target; if a crocodile is the longest-lived species in view and only an egg is present, focus on the crocodile egg. Ignore eggs or offspring only when the task explicitly asks for a particular life stage or explicitly asks for adult animals.

## Conductivity testing
Build a minimal series loop with one battery, one bulb, and the unknown substance. Use the known-good polarity order: connect battery anode to bulb cathode, then connect bulb anode through the substance and any wire terminals back to battery cathode. For a substance with terminal 1 and terminal 2, the reliable path is: battery anode -> bulb cathode -> bulb anode -> substance -> battery cathode. After the final connection, examine the bulb before you pick up or move the substance.

If the bulb is off, do not immediately declare the substance nonconductive. First verify the circuit:
- Examine the bulb, battery, and each wire/substance terminal to confirm they are connected in the loop above.
- Reverse the bulb's two connections once and examine the bulb again; ScienceWorld bulbs can be polarity-sensitive.
- Test the bulb with a known conductor such as a spare wire in place of the substance. If the bulb lights, restore the substance and re-examine. If the test bulb does not light, fix the circuit before testing the substance.
- If you picked up a switch, either wire it into the loop and activate/close it, or set it aside. A switch sitting unused in inventory does not complete anything.
Treat the bulb being off as evidence of nonconductivity only after you have verified the circuit works with a known conductor and the bulb is off only when the substance is in the loop.

## Plant growth and soil
For any grow-a-plant-from-seed task, do not search room-by-room for soil. Soil is created with the shovel outside.
1. Obtain the seed and focus on it if the task requires focusing first.
2. Go to the outside. If the shovel is in the greenhouse, pick it up first.
3. Run `use shovel on ground`.
4. Immediately run `look around`; you should now see `soil` nearby.
5. Run `pick up soil`.
6. Teleport to the greenhouse and run `move soil to <flower pot>`.
7. Move one seed into that same pot with `move <seed> to <flower pot>`.
8. Run `examine <flower pot>` to confirm it contains both soil and seed. If the pot already contains water, that is okay; do not pour it out.
9. Stay in the greenhouse and alternate `wait`/`wait1` with `examine <flower pot>` until the plant reaches the requested stage.
Do not plant the seed directly on the outdoor ground and wait. It will not grow without being moved into a pot with soil. For multiple seeds or plants, create fresh soil for each pot. Do not move soil from an already-planted pot into another if that would leave the first pot without soil. After each addition, examine the destination pot to confirm it contains its own soil and seed.

## Cross-pollination and fruit
When the goal is fruit or cross-pollination, plant at least two or three seeds in separate pots using the plant-growth protocol above. Grow them until the plants reach the flowering or adult stage. Then open the bee hive in the greenhouse to allow pollination. Continue alternating `wait`/`wait1`, `examine <flower pot>`, and `look around` until the requested fruit appears, then `focus on` the fruit.

## Getting unstuck
If you notice yourself repeatedly teleporting through rooms looking for an ingredient such as soil, paint, or a tool, stop and recall the creation or collection rule for that material. Use the environment to create what is missing, for example `use shovel on ground` for soil, rather than only searching containers.
<!-- SLOW_UPDATE_END -->

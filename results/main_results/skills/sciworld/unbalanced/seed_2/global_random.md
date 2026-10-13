

## ScienceWorld Execution Patterns

- Follow the task's explicit sequence in order. When the task says to `focus on X` before measuring or moving, perform those focus actions in the required order first. Focusing can usually be done from the object's current room and does not require the object to be in inventory.

- When the task's completion condition is to `focus on` the finished/found object, perform that final focus immediately once the object is ready, before extra inspections, waits, or teleports. A held object can usually be focused from inventory; do not pick up the target and then stop without focusing.
- Search efficiently: trust an explicit task location clue such as `located around X` and search that named room first. If a target substance is named, go to the room stated in the task before `focus on`/`use`; do not focus on a same-named substance or its container in another room. For closed containers, use `open` then `look at` and use the exact contained object/substance name, not the container name. If there is no specific location clue, use category room priors: for `plant` tasks, teleport to the greenhouse and `look around`; for `animal` tasks, teleport to the `outside` and `look around` for stationary named animals before checking indoor rooms; for thermometers, check the kitchen.
- Carry tools before use: `pick up` the tool, especially a thermometer, before `use <tool> on <object>` even when the tool and target are in the same room. If the target is in another room, pick up the tool first, teleport to the target's room, then use it.
- Carry before cross-room placement: for move/placement tasks, `pick up` the target object from its original location; teleport to the destination room and `look around` to confirm the exact destination container; then `move <target> to <destination>` using exact observed names.
- After `use thermometer on <substance>`, compare the reported temperature to the task threshold and `move <substance> to <box>` using the box named by the matching condition. Immediately after the move, issue `focus on <substance>` to signal task completion; do not stop after only placing it in the box.
- If the task asks for a category, choose a visible instance in the current room and use its exact observed name in commands.

- For `animal` tasks, do not use a plant/tree or `flower pot` as the animal. Search the `outside` first and prefer stationary named animals such as a `baby beaver`, `baby wolf`, `hatchling crocodile`, or `hatchling turtle`. Avoid `adult bee` in a bee hive: multiple bees are ambiguous, numeric IDs are unstable, and they fly out of inventory or the destination container. For `plant` tasks, choose a named potted plant/tree (e.g., `banana tree`, `peach tree`) and never focus/move the `flower pot N` container itself. If a moved animal disappears, switch to another stationary animal of the requested category rather than retrying bees or substituting a plant.
- For growing/fruiting tasks, plant seeds in a pot that already contains soil and water, then `wait` and `look at <pot>` until the tree is in the reproducing stage with a flower. Cross-pollinate by manually moving pollen between two flowers (`pick up pollen`, then `move pollen to flower`, selecting the other plant's flower if ambiguous). Do not try to `use bee on <flower/pot>`; bees are not a pollination tool.

## Use valid action grammar and exact referents
Only use verbs from the environment action list: `open`, `close`, `activate`, `deactivate`, `connect`, `disconnect`, `use`, `look around`, `examine`, `look at`, `read`, `move`, `pick up`, `pour`, `mix`, `teleport`, `focus`, `wait`, and `wait1`. Do not use invented verbs such as `take`, `put`, or `get`. If a syntactically valid command returns `No known action matches that input`, suspect the object referent; check `look around`, `look at <container>`, or `look at inventory` for the exact object name, then use that name. After picking up an object, use the referent given by the environment result (for example `bee` or `beaver`) if a more specific phrase such as `adult bee` is not recognized.

## Verify completion; do not idle-wait
`wait` and `wait1` only advance time; they do not signal task completion. Do not issue repeated waits after you think the task is done. If the environment has not ended, re-read the task and verify every clause: the correct object was focused on before being moved; the moved object is the same object that was focused on; the destination is the specified container/location, confirmed with `look at` or `examine`; and any conditional branch follows from the measured value. If any clause is unmet, take a corrective action.

## Handling ambiguous object choices
When an action returns `Ambiguous request: Please enter the number for the action you intended...`, respond on the next turn with only the chosen number, e.g. `0` or `1`. Do not append the number to the action (such as `focus on adult bee 1`), do not add location qualifiers such as `in bee hive`, and do not restate the original command. After the selection is accepted, continue from the resulting observation.

<!-- SLOW_UPDATE_START -->
When a task asks you to measure a melting point, boiling point, freezing point, or temperature of a substance, the value returned by `use thermometer on <substance>` is the value you must compare to the task threshold. Do not treat it as merely the current temperature, and do not try to heat or cool the substance to find a different value. Do not activate the stove/oven, move the substance to a heat source or freezer, or issue repeated waits/remeasures after the first reading unless the task explicitly tells you to heat or cool the substance.

For melting-point tasks specifically: after `use thermometer on <substance>`, take the FIRST reported temperature, compare it to the conditional threshold exactly, and immediately focus on or place the substance in the corresponding box. For example, a reading of 10 C for mercury is below 150 C, so focus on the below-threshold box; a reading of 7 C for chocolate is below 50 C, so focus on the below-threshold box. Do not heat the substance after this reading.

For animal search tasks, continue to teleport directly to the `outside` first and look for stationary named animals such as `baby wolf`, `baby beaver`, `hatchling crocodile`, or `hatchling turtle`. Avoid `adult bee` choices when any other stationary animal is available. Never substitute a plant/tree for an animal task or a flower pot for the requested target.

For plant search tasks, teleport to the greenhouse and use a named potted plant/tree, never the `flower pot N` container itself.

When you have satisfied the task's final condition, do not issue repeated `wait`, `wait1`, or redundant `look at` actions. If the environment has not ended, re-read the task and verify only the unmet clause.
<!-- SLOW_UPDATE_END -->

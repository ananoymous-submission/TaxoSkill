# General guidance

## Environment Guidance

- ScienceWorld may respond to a command with `Ambiguous request: Please enter the number for the action you intended (or blank to cancel):` followed by numbered choices.
- Use `pick up`, not `take`, to carry solid tools and target objects; do not try to `pick up` liquids.
- If an object is inside a closed container, `open <container>` and then `look at` or `examine` it to inspect the contents.
- Start by teleporting to the room named in the task, then `look around` to locate the target object/substance and nearby containers/devices.
- If a needed tool is not present, search likely rooms: the kitchen often has a thermometer, fridge, and freezer; the workshop often has batteries, wires, bulbs, and boxes.

## Execution Discipline

- When an ambiguous prompt appears, the next command should be **only** the number of the intended choice, e.g. `0` or `10`.
- Do **not** append the number to the original command (e.g. `open drawer 0` or `pick up avocado seed 0`) and do **not** repeat the action verb or add location details.
- Resolve the ambiguity immediately before issuing any next action.
- When choosing among alternatives, select the one matching the intended source/destination location, such as `(in inventory, in agent, ...)` when you mean the container you are carrying.
- If the same ambiguous prompt appears again, reply with the bare number that matches the intended referent.
- If an action fails with `No known action matches that input`, retry with an alternate referent from the observation: for recipes use a natural title/object name (`read instructions to make banana sandwich` or `read recipe`), not `read recipe titled ...`; for described objects use the base noun (`focus on pillow`, not `focus on white pillow`). Do not repeat the failing phrasing.
- Before using a tool on a target, have the tool available in inventory and be in the same room as the target; if needed, `pick up` the tool first (e.g. `pick up thermometer`, then `use thermometer on unknown substance B`).
- When moving between rooms, carry required tools and target objects in inventory.
- If `focus on <target>` fails with `No known action matches that input`, the target may be in another room or inside a closed container; locate/open it first, then retry the same `focus on` command.
- Many tasks ask you to "focus on X" multiple times, e.g. "First, focus on X. Next, focus on Y." Execute a separate `focus on` command for **each** named target, in the exact order given.
- Do not stop after focusing on only the first target. Continue until all required focus actions have been performed.
- When a multi-step task has a final answer object, ensure you finish by focusing on that answer object after the prerequisite actions.
- Do not skip focus calls while resolving ambiguity; finish the disambiguation by answering with the number, then issue the focus command.
- If you notice yourself repeatedly teleporting through rooms looking for an ingredient such as soil, paint, or a tool, stop and recall the creation or collection rule for that material. Use the environment to create what is missing, for example `use shovel on ground` for soil, rather than only searching containers.

# Task-specific guidance

## Find and Move Categorized Object Procedure

- For find-a-living/non-living thing tasks, choose any visible object that fits the category, `focus on` it, `pick up` the target, teleport to the destination room, locate the named box with `look around`, then `move` the target to that box.
- For final placement, first `pick up` the target, `teleport to` the destination room, `look around` to locate the named box/container, then `move <target> to <container>`.
- If the animal/egg or life-stage target is not visible in your current room, check `outside` early (`teleport to outside` then `look around`) before roaming through all indoor rooms. ScienceWorld commonly places animal eggs and adults outdoors, so this saves steps.
- Stop after moving the target to the named box.

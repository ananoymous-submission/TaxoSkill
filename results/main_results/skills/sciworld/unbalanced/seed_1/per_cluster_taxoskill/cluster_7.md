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

## Plant Growth and Soil

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

## Cross-Pollination and Fruit

When the goal is fruit or cross-pollination, plant at least two or three seeds in separate pots using the plant-growth protocol above. Grow them until the plants reach the flowering or adult stage. Then open the bee hive in the greenhouse to allow pollination. Continue alternating `wait`/`wait1`, `examine <flower pot>`, and `look around` until the requested fruit appears, then `focus on` the fruit.

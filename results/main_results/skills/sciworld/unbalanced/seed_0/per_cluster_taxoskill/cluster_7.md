# General guidance

## Action Grammar and Disambiguation
- Use only the listed action verbs: `pick up`, `move ... to ...`, `open`, `close`, `look at`, `examine`, `read`, `use ... on ...`, `pour ... into ...`, `mix`, `activate`, `deactivate`, `connect`, `disconnect`, `focus on`, `teleport to`.
- If an action returns `No known action matches that input`, do not repeat it. Rephrase with the allowed grammar: to retrieve an item from a container use `pick up <item>` or `move <item> to <location>`, not `take <item> from <container>`.
- On an ambiguous-request prompt with numbered options, issue only the number of the desired option as the next action. When multiple identical objects exist, choose the option whose location text matches where the desired object currently is. For a carried item the desired location is `inventory, in agent, in <current room>`; for an item still inside a container/pot it is `in <container>, in <room>` or `in <pot>, in <room>`.
- Avoid re-issuing the same failed command; switch to a different valid action form or examine the object/container first.
- Before searching broadly, teleport to the room implied by the task or object category and `look around` once: `art studio` for paints, `greenhouse` for plants/seeds/pots/soil, `kitchen` for foods/thermometer/recipe, and the stated destination room for boxes. Only check other rooms or closed containers if the target is not visible there.
- If the target is not visible, check closed containers in the current or implied room by first `open <container>`, then `look at <container>`. A closed fridge, cupboard, closet, or paint closet does not reveal its contents to `look around` alone. If `look around` already shows a container's contents (for example `a seed jar (containing ...)`), skip `open` and `pick up <target>` directly.
- If `focus on <object> <descriptor>` fails with `No known action matches that input`, retry with the shortest base object name (for example `focus on apple tree`) and then select the numbered option whose location text matches the desired object.
- When a numbered choice yields a specific generated item name (for example `bee 2`), use that exact name for the next commands instead of the generic category name. If that name is unknown, use `look at inventory` or `look around` to get the current object name.

## General Completion and Hard Stop
- Stop after moving the required object to the required box or container; do not wait, re-check it, or replace it. Post-task state changes such as a plant becoming 'unwell' do not mean the task needs redoing unless the task explicitly requires keeping it alive.
- Once you have issued the task-final action (final `focus on`, final box placement, final pollination, or other required completion signal), take no further actions. Do not call `wait`, `wait1`, `examine`, `look at`, `use thermometer`, or repeat the same final action.
- After the observation confirms the final required action has succeeded (for example `move X to Y`, `focus on X`, or final box placement), emit no more actions. Do not call `wait`, `wait1`, `look around`, `look at`, `examine`, `use thermometer`, or repeat the final command.
- Repeating a completed final action or waiting after it wastes steps and causes truncation. If the current observation already confirms success, stop immediately.
- Never express stopping by issuing `wait1`. If your reasoning says the task is complete, stop immediately with no action.

# Task-specific guidance

## Water
- To collect water from a sink: `activate sink`, `move <container> to sink`, then `pick up <container>`.
- If a sink is broken, try another room's sink first: `activate sink`, `move <empty container> to sink`, then `pick up <container>`. For a bathtub, activate it, close the drain, wait until water appears, move a container into it, then pick it up.

## Plant Setup and Growth
- Focus on a seed if asked, then `move <seed> to <pot>` that contains soil.
- Prepare soil in all pots before planting any seeds. If available pots contain only water, first obtain soil/dirt from the ground outside using a shovel/examine and move it into the pot before planting.
- Plant all seeds, keep the pots watered, then `wait` and inspect all pots each cycle until the required stage. Track stages: seed -> seedling -> adult -> reproducing.

## Cross-Pollination and Fruit
- For cross-pollination, wait until all required plants are in the reproducing or flowering stage before moving pollen.
- When plants are in the reproducing stage and show flowers, manually `pick up pollen` from one flower, choose the inventory pollen option, then `move pollen to flower` on a different plant.
- After transfer, `wait` and `look at <pot>` for the grown fruit/named object before focusing on it.
- Complete by focusing on the specified fruit once it appears: issue the final `focus on <fruit>` once and stop.

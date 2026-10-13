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

## Electrical Conductivity Testing

- First `examine` the battery, wires, bulb, and test object once to learn their terminals (`anode`/`cathode` or `terminal 1`/`terminal 2`). If `examine <test object>` does not show terminal or material info, do not repeat the same examination; proceed to connect wires to `<object> terminal 1` and `<object> terminal 2`.
- Build one closed series loop only: battery anode -> wire1 -> test object -> wire2 -> bulb anode -> bulb cathode -> battery cathode.
  - `connect battery anode to <wire1> terminal 1`
  - `connect <wire1> terminal 2 to <object> terminal 1`
  - `connect <object> terminal 2 to <wire2> terminal 1`
  - `connect <wire2> terminal 2 to <bulb> anode`
  - `connect <bulb> cathode to battery cathode`
- If a switch is available, include it in series from the start and `activate switch` once before the first bulb exam. Do not add a switch later.
- Do not put the test object into inventory during diagnosis.
- If a connection fails because a terminal is already connected, `disconnect <component>` at the object level before reconnecting.
- After building, `examine <bulb>` once. Do not re-`examine` the same bulb/component repeatedly when it keeps returning the same off/unlit state; that state is not progress.
- A lit bulb means conductive: place the object in the conductive box and stop.
- If the bulb is off, verify with exactly one short. `disconnect <test object>` only, connect the same two wire terminals that went to the object directly to each other, and `examine <bulb>` once. If the bulb now lights, place the test object in the nonconductive box and stop.
- If the shorted circuit is still off, fix the circuit before classifying: inspect the series connections only once, repair at most one obvious open, and try at most one alternate component total, either one bulb or one wire. Do not try a bulb and then a wire, do not try every color, and do not rebuild or re-short the same circuit again. Inspect component connections only once after that; if the intended series loop is intact, do not keep rebuilding the same circuit.
- If the bulb is still dark after that, then stop diagnosis and proceed to the final classification/placement instead of spending further actions re-examining the same off bulb or endlessly rewiring.
- After that budget is spent, stop circuit work permanently. Use `look at <test object>` once to identify its material. Metal objects are conductive; wood, plastic, ceramic, rubber, glass, food, and fabric are nonconductive. If the material is still unknown, make a single best box placement from any clue you have and stop. Re-examining the same off bulb is never progress.
- For final placement, after the diagnosis budget is spent pick up the test object only for immediate final placement, or issue `move <test object> to <box>` directly. Stop after the final box placement.

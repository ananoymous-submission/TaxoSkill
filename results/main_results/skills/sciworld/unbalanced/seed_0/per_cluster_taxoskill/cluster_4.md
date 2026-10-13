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

## Change State of Matter

## Thermometer Prerequisite
- Before using `use thermometer on <substance>`, ensure the thermometer is carried; it only works from inventory. If needed, teleport to the kitchen, `look around`, `pick up thermometer` (even if it is already visible or `focus on thermometer` succeeds), then `focus on thermometer`.

## Heating/Cooling Setup
- Before heating or cooling, put the substance in a movable container such as a cup, bowl, or pot. If it melts, move the container rather than trying to pick up or pour the liquid.
- Prefer active devices (stove, oven, freezer) over passive waiting to change temperature quickly.
- Use `wait1` (one iteration) while heating or cooling, then check temperature and phase after each step. Avoid `wait` (10 iterations) on an active hot stove/oven; it overshoots the threshold, can set the sample on fire, and makes it hard to cool back down.
- Stop heating as soon as the sample is near or just beyond the requested threshold; check phase at that temperature and answer above/below.
- If liquid is stuck on a hot appliance, do not repeat failed `pour` attempts; deactivate the appliance and move the container/cool it as soon as possible.

## Freeze Tasks
- For freeze tasks, after focusing on the substance, put it in a freezer: `open freezer`, `move <substance> to freezer`, then `wait` and `examine <substance>` until solid.
- After moving the substance into the appliance and waiting once, confirm with `use thermometer on <substance>`. If the measurement indicates the target phase/temperature has been reached, do not loop further `examine`/`focus` commands; issue the task's required final `focus on` once and stop.

## Melt and Melt-Then-Freeze Tasks
- For melt-then-freeze tasks, melt first in an oven/stove only until the substance becomes liquid; do not leave it heating to the point of fire.
- If it catches fire, remove it from the hot appliance and deactivate the appliance before cooling it.
- Monitor progress with `use thermometer on <substance>`; once the desired phase is reached, move the container/substance to the next appliance or focus as required.

## Boil / Evaporate Tasks
- For boil or evaporate tasks: once the thermometer reads above boiling point, stop checking the liquid. Focus on the gas phase name once if one appears; otherwise focus on the original substance once and stop.

## Melting-Point Threshold Variants
- Distinguish between current temperature and melting point. A hot liquid is not evidence that its melting point is high.
- If the task only asks whether a melting point is above or below a threshold, do not chase the exact melting point through repeated heating/cooling cycles.
- First observe the sample's current phase and temperature; if its phase already implies the answer, decide immediately. For example, a substance that is liquid at a temperature well below the threshold must have a melting point below that observed temperature.
- Otherwise bring the sample near the threshold using a heating/cooling device, monitor with the thermometer, and `examine` the sample's phase: solid at the threshold means the melting point is above it; liquid at the threshold means the melting point is below it.
- Keep the sample in a movable container. Use only `wait1` on an active appliance; after each `wait1` check `use thermometer` and `examine <substance>` once each.
- Stop heating and deactivate the appliance as soon as the transition brackets the threshold. Move the container off the hot appliance immediately.
- Classify with one clean phase observation at the threshold: liquid at the threshold means below; solid at the threshold means above. Then focus on the corresponding box once and stop. Never leave a melted sample on a hot stove or oven.
- If `examine <substance>` or `look at <container>` returns only the name and does not state solid/liquid/gas, do not keep re-checking. Classify once from the measured temperature at the threshold plus broad melting-point knowledge, then issue the final box focus.

## Final Focus and Stopping
- For heating or cooling state changes, the final required action is normally one `focus on` for the task-named substance or generated phase name. Issue it once as soon as the phase has changed and stop.
- For freeze or melt tasks: after moving into the appliance and waiting once, confirm with `use thermometer` once. If the target phase is reached, issue the required final `focus on` once and stop.

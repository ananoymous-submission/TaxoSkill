# General guidance

## ALFRED Command and Recovery Rules

- Issue the admissible command exactly as shown.
- Treat `Nothing happens` as a signal that the previous command was not effective. Retry the command at most once. If it still fails, change strategy instead of resending the same command.
- When a `Nothing happens` occurs, check: exact current admissible-action wording, whether you are already at the location, whether a container needs opening, and whether you are holding the wrong object.
- Do not let an unneeded or empty held object consume more than two recovery actions.

## Search and Completion Control

- Before exhaustively opening long rows of same-type containers such as numbered cabinets or drawers, inspect visible open surfaces first: coffee tables, side tables, dressers, shelves, sofas, armchairs, and countertops. Small goal objects such as keychains, credit cards, mugs/cups, and remotes are often found there.
- After checking a few empty same-type containers, switch to another surface or container category instead of opening every numbered instance in order.
- After executing an action that should satisfy the task, stop issuing confirmatory `look`, `inventory`, open, or close commands. If the environment has not ended, that means the goal is not yet satisfied: re-evaluate object identity, quantity, state, or destination candidate instead of announcing completion again.
- Do not reject the only visible related object solely because its label differs from the goal noun, but also do not declare completion with it until the environment confirms success. If the environment does not end after using that candidate, search remaining locations for the exactly named object.

## Single-Item Carry Limit

- You can carry only one object at a time.
- If `take <object> from <place>` returns `Nothing happens` while you are already carrying something, deposit or deliver the held object first, then retake the next object.

# Task-specific guidance

- The `put` template uses the literal token `in/on` (for example `put mug 1 in/on cabinet 1`). Do not split it into `put mug 1 in cabinet 1` or `put mug 1 on cabinet 1`.
- For cooling/chilling/refrigerating, use the canonical action and appliance: `cool <object> with fridge`. Do not substitute a different state-change action or appliance for the one required by the task.
- Hold the target object while issuing the direct transformation command; do not place the object inside the appliance and then rely on a generic `use <appliance>`.
- Only after the transformation is confirmed, go to the target receptacle and `put <object> in/on <receptacle>`.
- If `put` fails after using the exact `in/on` template, leave the object and resume the task rather than entering a close/open/put loop.
- For goals that require two or more objects, transport one item at a time to the destination, put it down, and only then return for the next item.

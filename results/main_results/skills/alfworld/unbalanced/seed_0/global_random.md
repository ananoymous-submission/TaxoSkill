

## ALFWorld Command Failure Recovery
- Treat `Nothing happens.` as a rejected command. Do not reissue the same command or alternate between near-identical rejected variants.
- After any rejection, run `look` or `inventory` to re-synchronize state, then choose a different action type: change the verb, preposition (`in` / `on` / `from`), target, or receptacle.
- For any single subgoal, after at most two rejected attempts, move on to the next candidate object or location. Revisit the failed subgoal only if no other progress is possible.

## ALFWorld Search and Collection Strategy
- Do not pick up non-target containers unless you need to inspect them for a target. If you accidentally take one and cannot put it down, abandon placement attempts after one or two failures; holding irrelevant objects is usually not fatal.
- When a target object is visible on a surface, attempt to take it immediately (`take <target> from <surface>`). If the direct take fails, run `look`/`inventory` and try one alternate take command before moving to another candidate.
- Track how many target objects you have collected. Once you have the required number, move directly to the goal receptacle and place them.

## ALFRED/ALFWorld Object-Transport Patterns

- Parse the task into target object type, required quantity (`a`/`some` = 1, `two` = 2), and destination receptacle.
- Use exact object and receptacle IDs exactly as they appear in the latest observation. Do not rephrase or omit IDs.
- Move to a candidate surface or container before inspecting or opening it.
- Search systematically: start with likely or semantically typical locations for the target object type, then inspect other candidate surfaces/containers without revisiting already-checked locations. Move on after an empty result.
- Open closed containers such as drawers, cabinets, and safes before checking their contents; contents are revealed only after opening. If the destination receptacle is closed, open it before placing an object.
- When the target object is observed, take it with `take <object> <id> from <receptacle> <id>`.
- Place objects with `put <object> <id> in/on <destination> <id>`. Use the literal `in/on` form; plain `in` or `on` may fail.
- Assume a one-object carry limit. For multi-object tasks, transport one item at a time: take one, go to the destination, put it down, then return for the next item.

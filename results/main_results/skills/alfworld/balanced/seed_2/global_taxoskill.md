

## Break Failed-Action Loops
- Treat `Nothing happens` as an invalid action in the current state. Never repeat the identical command; it will not succeed on retry.
- After a failed command, choose a different option from a different category: change the verb (`cook` vs `heat`), change the source/receptacle, check `inventory`, or examine the current location once.
- If two attempts with the same tactic fail, abandon that tactic and switch to another appliance, container, or object.
- Before re-attempting a failed interaction, ensure the target container is open/closed and the object is where you believe it is.

## Object Targeting and Inventory Management
- You can carry only one object at a time. Take only the exact object class named in the task: if the task says `cloth`, pick up an object named `cloth`, not `towel` or `handtowel`.
- Before taking a new object, check `inventory`. If you are holding a non-target object, put it back in/on the exact receptacle where you found it, or another valid receptacle, before taking the target.
- If `take <object> from <receptacle>` fails with `Nothing happens`, first check whether you are holding something and whether the receptacle is open; do not simply walk away and repeat the same take.

## Efficient Search in ALFWorld
- Avoid opening every cabinet or drawer in numerical order. Check visible surfaces first, then open only receptacles that could plausibly contain the target object class.
- If the target is food or tableware, check the fridge and relevant cabinets/countertops early instead of exhausting all cabinets first. If the target is cloth or linen, check shelves and drawers early.
- After a few unsuccessful locations in the same fixture type, switch to another likely fixture or closed container.
- When the target is found, stop searching and begin the required transformation/delivery immediately.

## Transformation Verbs
- Take the target object first, then issue the explicit held-object command: `clean <object> <id> with sinkbasin <id>`, `cool <object> <id> with fridge <id>`, or `heat <object> <id> with microwave <id>`.
- The appliance does not need to be opened or the object placed inside first; the direct `with` command works.

## ALFWorld Task Routines
- **Simple delivery** (`put some <object> on/in <surface>`): find a visible `<object>`, `take <object> <id> from <surface>`, `go to <destination>`, then `put <object> <id> in/on <destination>`.
- **Transformation tasks** (`clean/cool/heat some <object> and put it ...`): take the target object first, go to the relevant appliance, and use the explicit held-object or placed-object command from the Transformation Verbs section above. Do not put the object inside the appliance and then try a generic `use <appliance>` action.
- **Desklamp tasks** (`look at` / `examine` an object with a desklamp): locate the desklamp, usually on a sidetable or desk; take the target object; go to the desklamp location; and run `use desklamp <id>`. No separate `look at` command is needed. If the target is elsewhere, retrieve it and return to the desklamp location.
- **Multiple objects**: deliver one object at a time to the final destination before searching for the next object.

## ALFWorld Exact Placement Syntax
- To place an object in or on a receptacle, use the literal preposition `in/on`: `put <object> <id> in/on <receptacle>`. A command using only `in` or only `on` may return `Nothing happens` even when the receptacle is open and you are holding the object.
- If `put <object> <id> in <receptacle>` fails, immediately retry with `put <object> <id> in/on <receptacle>` before changing cabinets, reheating, or re-examining the object.

## Stopping and Avoiding Observation Loops
- After the required object state and delivery are satisfied, stop emitting actions. Do not repeatedly call `look`, `inventory`, `examine`, or open/close the destination once the object is confirmed in/on the destination.
- If observations stop changing but the task is not complete, change something meaningful: verify exact syntax, verify the exact target object class, or verify the receptacle state. Do not repeat the same no-op observation command.

<!-- SLOW_UPDATE_START -->
<!-- SLOW_UPDATE_END -->

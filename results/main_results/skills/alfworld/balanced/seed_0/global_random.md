

## ALFWorld Execution and Recovery Guidelines

### 1. Search efficiently; avoid brute-forcing all containers

- Use the initial observation to identify visible surfaces and containers. Skip `look` from the initial middle-room position; move immediately to the most likely visible surface for the target object type.
- The step budget is limited. Check all visible surfaces and locations relevant to the task before exhaustively opening every cabinet, drawer, or other container.
- Track what you have already visited and checked. Do not revisit cleared containers or repeat `go to X` when it returns `Nothing happens`; instead try `open X` / `examine X` from your current position.
- If a single container type is not yielding the target after 2-3 attempts, stop opening more numbered containers of that type and broaden search to visible surfaces such as countertops, shelves, tables, dressers, desks, or sidetables.

### 2. Respect the one-object inventory limit
- You can carry only one object at a time.
- Before taking a second object, check `inventory`. If already carrying something, put the held object in/on a valid surface or target receptacle first, then retry the pickup.
- Do not repeatedly retry a failed `take` while your inventory is full.

### 3. Recover from `Nothing happens` deliberately
- A failed action means change something. Stop after at most two identical failed attempts.
- Diagnose one variable at a time: check `inventory`, check your location with `look`, examine the relevant receptacle/object, and ensure the exact observed object and receptacle names are used.
- Prefer commands from the current admissible actions. If the desired action is not currently available, change state first by putting down a held object, opening a container, or moving to the correct location.
- Use ALFWorld command forms:
  - `put <object> in/on <receptacle>` rather than bare `put <object> on <receptacle>`
  - `clean|cool|heat <object> with <receptacle>`
  - `take <object> from <receptacle>`
- Match the task noun exactly: do not substitute towel/handtowel for cloth, or mug for cup.

### 4. Deliver/place objects promptly
- When at a target receptacle and holding a relevant object, place it in/on that target as soon as possible rather than carrying it while continuing to search.

- For multi-object tasks (`find two X and put them in Y`), use a fetch-deliver cycle: take one instance, go directly to the target, put it, then return to the source or another likely surface for the next instance. Never attempt to carry two objects at once.
- Once all required objects are placed, stop; the task is complete.

## Core ALFWorld Task Loop

- Break each task into: locate target, take target, apply any required transformation or examination, navigate to the destination, and perform the final `put` or `use` action.
- Always refer to the exact object and receptacle IDs present in observations (e.g., `book 4`, `fridge 1`, `sidetable 1`).
- Issue one action at a time from the currently admissible actions.

## Container Handling and Search Prioritization

- Prefer locations semantically associated with the target object type (e.g., pens in drawers/sidetables, mugs in cabinets/countertops, books/lamps on desks/sidetables).

- In kitchens and bathrooms, check countertops very early: small items such as soapbars, dishsponges, toiletpaper, potatoes, and plates are often placed there rather than inside containers.

- For kitchen target objects (plate, bowl, mug/cup, apple, potato, fork, spoon, knife, etc.), before opening more than 2-3 closed containers follow this priority: (1) all countertops, (2) **sinkbasin**, (3) other visible surfaces in the current room (tables, shelves, dressers, desks), (4) task-relevant appliances only if the target is plausibly stored/cooled/cooked there.
- HARD STOP: after opening 2-3 cabinets/drawers without finding the target, do not continue opening more numbered cabinets/drawers. Immediately visit the next unchecked visible surface from the priority list (for kitchen plates/cups/bowls, check `sinkbasin 1` and any remaining countertops) and use `examine` or `take <object> from <surface>` before returning to containers.
- Never open every numbered cabinet in sequence. If a `go to cabinet <n>` returns `Nothing happens`, try `open cabinet <n>` from the current location, but keep the hard stop count.
- When a container is closed, open it before inspecting or taking from it. If the destination container is closed, open it before using `put <object> in/on <destination>`.

- Extend surface-first search priority to other room types before opening closed containers:
  - Bathroom targets (soapbar, toiletpaper, tissuebox, candle, towel): countertop, sinkbasin, dresser, then drawers/cabinets.
  - Living/bedroom targets (remotecontrol, newspaper, pencil, pen, keychain, cellphone, watch, creditcard, alarmclock): coffeetable, tvstand, sidetables, diningtable, dresser, shelves, sofa/armchair, then drawers.
- Small items such as soapbars, dishsponges, toiletpaper, potatoes, plates, butterknives, and cloths are often on visible surfaces rather than inside closed containers.
- For multi-object tasks (`two X`), clear all relevant visible surfaces in the priority group before moving to containers; the second instance is often on another visible surface.

## Transformations, Cleaning/Cooling, and Examination Tools

- For transformation tasks, retrieve the object, go to the appropriate appliance, and open it first if it is closed (e.g., `open microwave 1`, `open fridge 1`) before issuing `<verb> <object> with <appliance>` while holding the object (e.g., `heat egg 2 with microwave 1`, `clean apple 1 with sinkbasin 1`, `cool <object> with fridge 1`).
- After a clean/cool action, the object normally remains in inventory; do not assume it was left inside the appliance.
- Then navigate to the destination and place the object with `put <object> in/on <receptacle>`.
- For desklamp examination tasks, locate the surface containing the target object and desklamp, turn on the lamp with `use desklamp 1`, and take the target object from its surface; the order of turning on the lamp and taking the object is flexible.
- For other instrument tasks such as examine/look at with an instrument, separately locate the target and instrument, take the target if movable, go to the instrument, and then `use <instrument>`.

<!-- SLOW_UPDATE_START -->
<!-- SLOW_UPDATE_END -->

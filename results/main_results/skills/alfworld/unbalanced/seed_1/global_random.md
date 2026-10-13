

## ALFRED Object-Relocation and Search Heuristics

### Core object-relocation workflow
For `put <object> in/on <destination>` tasks:
1. `go to <source>` to bring the source into view.
2. If the source is a closed receptacle such as a drawer, cabinet, or safe, `open <source>` before taking.
3. `take <object> from <source>`.
4. `go to <destination>`.
5. If the destination is a closed receptacle, `open <destination>` before placing.
6. `put <object> in/on <destination>`.

Always select exactly one admissible action and update the plan from each new observation.

## ALFWorld Step-Budget and Search Strategy

- Parse the task into required object(s) and their required count (e.g. `a`, `some`, `two`), any required object-state modifier (e.g. `cool`, `clean`, `cooked`, `sliced`), and the final destination before moving. Track how many target objects have been placed and keep retrieving until the required count is met.

- Treat `some` as a single required instance unless the task wording explicitly requires a count such as `two`, `three`, or `a pair of`; do not over-collect.
- Prioritize the most semantically plausible receptacles for the target object first, rather than sweeping every cabinet/drawer/countertop in numeric order.

- Use object-category location priors to start the search: remotes, laptops, tissue boxes, keys, and watches are often on coffee/side/dining tables or dressers; toiletries and cleaning products are often in bathroom cabinets or on countertops; pepper shakers and vases are often in kitchen cabinets or on dining/side tables/dressers. Before opening long rows of drawers or cabinets, exhaust open surfaces and furniture strongly associated with the target object (e.g. remotes near sofas/tvstands, toiletries on countertops/carts, produce on countertops, small items on dressers/sidetables).

- Extend object-category and visible-surface priors before opening long rows of drawers or cabinets: credit cards and CDs are often on dining/side tables or dressers; bread is often on dining tables or countertops; pillows are often on sofas, armchairs, or beds; toiletpaper is often on toiletpaperhangers, toilets, or bathroom countertops/carts; pens, pencils, books, and alarm clocks are often on desks, dining tables, shelves, beds, and sidetables. Check these open surfaces early, especially when they are the task destination or nearby.
- Keep a record of receptacles already checked and their contents. Avoid revisiting empty locations unless new information justifies it.
- After locating all required objects, stop exploratory searching and immediately complete any state-change and final-placement steps.

## Recovering from Ineffective or Rejected Actions

- Treat `Nothing happens` as a rejected or ineffective action. Do not immediately retry the same command or near-identical command repeatedly.
- Reorient by using `look` or `inventory`, then infer the missing precondition: for example, open a closed container before taking from it, or move to the correct object/receptacle before acting.
- If an object cannot be taken from a location after a rejected attempt, leave that interaction and search elsewhere; repeated retries of the same object/location waste the step budget.

### One carried object at a time
The agent can carry only one object. For tasks requiring two or more objects, proactively complete the full fetch-and-place cycle for the first located object before searching for the next, even if the next object's location is already known. Do not attempt to take a second object while carrying the first; deliver the carried object to the final destination or a temporary surface first, then return for the next object. If a `take` of a second object still fails with `Nothing happens`, do not retry the same command; run `inventory`, unload as above, and only then reattempt the next object. If a location is known to contain multiple required objects, return to that same location after each delivery instead of searching elsewhere.

## Multi-instance search and sweep limits

- Parse plural object requests (`two keychains`, `three mugs`, `a pair of ...`) as requiring that many distinct instances, not one.
- After finding one instance, do not start a numeric drawer/cabinet sweep. First inspect all other visible/open receptacles and furniture surfaces in the room that could hold the object type before opening further closed storage.
- Cap closed-storage sweeps at three consecutive unhelpful receptacles: if three consecutive drawers/cabinets are empty or contain only unrelated objects, stop the numeric sweep immediately. Reorient with `look` or `inventory`, then revisit not-yet-inspected open surfaces and appliances (countertops, sinkbasin, stoveburners, fridge, tables, dressers) before opening any more numbered cabinets/drawers.

<!-- SLOW_UPDATE_START -->
<!-- SLOW_UPDATE_END -->

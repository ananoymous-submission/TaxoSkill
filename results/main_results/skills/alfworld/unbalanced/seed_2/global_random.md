

## Efficient Search and Truncation Avoidance
- Before opening closed storage one by one, inspect visible/open surfaces first. Use `look` to re-read the current area, and `go to`/`examine` task-relevant open receptacles (countertops, stoveburners, tables, sinkbasin, shelves) when available.
- Use object-location priors to order search: cooking/serving items (pans, pots, plates, mugs) are often on or near stoves, countertops, or tables; utensils and small objects are more often in drawers; cold food/drink is often in the fridge. Check the matching high-probability receptacles before lower-probability closed storage.
- Do not exhaustively open cabinets, drawers, or other containers in numeric order. After a few high-probability locations and matching receptacles fail, re-scan overlooked open surfaces before continuing with the remaining containers.
- If many steps have been spent opening containers without progress, switch receptacle category or re-read the task for the likely source/destination rather than continuing the same exhaustive sweep to the end.

## Command Construction
- Use the exact object and receptacle IDs exactly as they appear in the current observation or admissible actions (e.g., `soapbottle 2`, `countertop 1`).
- Prefer the full admissible forms: `take <object> <id> from <receptacle> <id>` and `put <object> <id> in/on <receptacle> <id>`.
- Always use the combined preposition `in/on` for put actions. Separate `put ... in` or `put ... on` forms can fail; if one fails, switch to the combined `in/on` form.

## Closed Receptacle Handling
- For closed storage such as cabinets or drawers, `go to <receptacle> <id>` and then `open <receptacle> <id>` before checking contents or taking from it.
- Move on immediately from empty or irrelevant receptacles; do not retry the same search or open action after it has failed to reveal the target.

## Single-Object Inventory and Multi-Item Tasks
- The agent can carry only one object at a time.
- For multi-item tasks, shuttle one item at a time: take, go to the destination, put, then return for the next item.
- If a second `take` fails with `Nothing happens` while an object is already held, check `inventory`, deliver the held object first, and then retry the failed take.
- After picking up an object, navigate to the destination before attempting to put it.

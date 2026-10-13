# General guidance

## Open closed receptacles before taking or placing
Before taking an object from or placing an object in/on a closed receptacle such as `fridge`, `drawer`, `cabinet`, or `microwave`, check the observation and open it with `open <receptacle>` first, unless you are using a direct `heat`, `cool`, or `clean` transformation command (which succeeds with the appliance closed). Open surfaces such as `countertop`, `shelf`, `desk`, `diningtable`, `sinkbasin`, `garbagecan`, `stoveburner`, and `toilet` usually do not require opening before `put`. Use the observation wording as the cue: if it says `The <receptacle> is closed`, call `open` before `put` or `take`; if it says `On the <surface>, you see ...`, you can interact or place directly without opening.

## Stop after task completion and break observation loops
Do not issue the same observation command (`look`, `inventory`, `examine`) twice in a row unless the situation has changed. After the action that satisfies the task's goal (e.g., the final `put`/placement, or the final `heat`/`cool`/`clean` if no placement follows), stop acting immediately. Do not close receptacles, do not call `look`, `inventory`, `examine`, `use`, or `go to` to verify; extra actions after completion cause truncation. If you think 'no further action is needed', make no further tool call.

## Carry only one object at a time
ALFWorld permits carrying only one object at a time. Do not try to hold two objects at once; a failed `take` while already carrying an object is usually the one-object carry limit, not a navigation problem.

## Handle `Nothing happens` without retrying
`Nothing happens` means the last command had no effect, not that the task has failed. Do not repeat the same command. Treat it as a failed attempt and choose the next useful action: try a different object/location, try a different action for the same object (for example `use` instead of `take` for a fixed tool), or continue with the next candidate in a search.

## Search efficiently and avoid exhaustive opening
When searching for a task object, check open surfaces/fixtures first (`countertop`, `shelf`, `desk`, `diningtable`, `sinkbasin`, `stoveburner`, `dresser`, `sidetable`, `bathtubbasin`, `toilet`, tables) because most task objects are visible there. Use the initial observation's list of receptacles to navigate directly to likely locations; starting with `look` often returns only `You see nothing` and wastes an action. Do not open every closed receptacle in numerical order; use the object type and room layout to choose likely locations. If a likely surface is empty, move on. Once you find a matching object, stop searching and continue with the task.

## Match the requested object type exactly
ALFWorld object classes are exact, so a `mug` is not a `cup`, a `bowl` is not a `plate`, a `pan` is not a `pot`, etc. When the task asks for a specific object (e.g., `cup`), search for and use an object whose name is exactly that type; do not take a similar object as a "type of" the requested one. If you notice the exact object later, switch to it.

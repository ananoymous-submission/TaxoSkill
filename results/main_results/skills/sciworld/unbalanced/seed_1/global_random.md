

## Resolving ambiguous references and using exact object identities
When an action returns an `Ambiguous request` with numbered options, reply with just the number of the chosen option, e.g. `0`. Do not append the number to the original command; forms like `focus on adult bee 0` are usually invalid.

When choosing among numbered options, read each option's parenthesized location/description and select the instance that matches the object you intend to act on (for example `focus on adult bee (in bee hive, in greenhouse)`). Do not reuse an earlier option number assuming it still refers to the same object; the list and numbering can change between prompts.

After a successful pickup, record the exact object reference shown in the observation, e.g. `You move the bee 4 to the inventory`. Use that exact reference in later commands such as `move bee 4 to green box`, not generic labels like `adult bee` or `bee`. If a move command fails, immediately `look around` and inspect the target container/location to find the object's current exact reference. Living objects may appear in a room even when not shown in inventory.

For living targets such as adult bees, the numeric pickup labels (`bee 1`, `bee 4`) are ephemeral and often fail after teleporting. If `move bee <N> to <box>` fails, prefer the visible generic label in the current room (`move adult bee to <box>`) rather than retrying the number, checking inventory, or teleporting back and forth.

## Multi-room object-moving tasks
When the task requires moving an object to a container in another room, first complete any required focus or measurement steps on the object. Then pick up the target using an unambiguous exact reference. After each teleport, especially into the destination room, run `look around` to refresh visible object names and confirm the exact target container name before issuing the next command. Then use `move <exact object reference> to <container>`. Do not re-focus or re-pick-up the object after it has been placed in the final container unless the task explicitly requires it.

Focus on only one target object—the one you are about to move—and avoid focusing on multiple candidates. Move that same object immediately after focusing or picking it up. After moving, perform a single verification such as `look at <container>` or `look around`, and if the target is present, do not keep issuing `wait`, `look around`, or `look at` commands; repeated extra steps can cause a terminal failure.

For `find a(n) <category>` tasks, first check the current room and use an obvious matching object if one is visible. If not, teleport to a likely room and `look around` again. In ScienceWorld, plants and many living things are in the greenhouse; animals are often hidden inside the greenhouse's closed `bee hive`, so `open bee hive` and then `look at` or `examine` it to reveal adult bees before focusing or picking one up. Prefer a visible, unambiguous example of the requested category rather than searching exhaustively.

## Using instruments to measure objects
Before using an instrument such as a thermometer on a target, ensure the instrument is in your inventory or otherwise present in the current room. If it is in another room, pick it up first, then teleport to the target and issue `use thermometer on object`.

For temperature-measurement tasks, follow the task's focus order before measuring: after obtaining the thermometer, `focus on thermometer`, teleport to the target, `focus on <substance>`, then `use thermometer on <substance>`. Compare the measured temperature to the stated threshold before choosing the destination box, and pick up the target only after measuring.

## Electrical connections and conductivity testing
ScienceWorld `connect` commands require connection points. Unpolarized components such as wires and metal objects use `terminal 1` and `terminal 2`; polarized components such as batteries and light bulbs use `anode` and `cathode`. Valid syntax examples include:
- `connect battery anode to black wire terminal 1`
- `connect black wire terminal 2 to metal fork terminal 1`
- `connect blue light bulb cathode to battery cathode`

After building a circuit, `examine` each component to verify the complete path. A bulb remaining off is not sufficient evidence that a tested material is nonconductive: first confirm every connection is correct, the circuit is closed, and any switch is both connected and activated.

## Stop after task completion
After any action returns a clear success such as `You move <object> to <box>` or otherwise satisfies the final task condition, stop immediately. Do not issue any further `look at`, `look around`, or `wait` actions; post-success waits and look loops caused terminal failures.

<!-- SLOW_UPDATE_START -->
<!-- SLOW_UPDATE_END -->

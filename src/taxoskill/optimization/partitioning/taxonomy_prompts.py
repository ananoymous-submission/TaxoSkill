"""Prompt templates used by the taxonomy pipeline.

Generation, update, and review share one rules block. Assignment uses a short,
standalone prompt to select from existing types.
"""


# -----------------------------------------------------------------------------
# Shared rules for generation, update, and review
# -----------------------------------------------------------------------------

SHARED_RULES = """**Purpose**

Group tasks by the skill the agent needs to learn to solve them. Each type should have a short name and a one-sentence definition describing what the agent needs to do.

**Grouping**

- Tasks belong to the same type when the same skill instructions can solve them.
- Different objects, locations, or quantities do not create a new type unless they change how the task must be done.
- Using the same tool or sharing some steps does not mean tasks require the same skill.

**Merging**

- Merge types that require the same skill.
- If one type's skill already teaches everything needed to solve every task in another type, merge the covered type into the covering type.
- Do not invent a broader skill that teaches two different procedures just to merge them.

**Splitting**

- Split a type when its tasks require different procedures, rather than different parts of the same procedure.
- Do not split if one procedure already covers the others. Simpler tasks may use only part of that procedure.

**Tasks requiring multiple skills**

Do not create a separate type merely because a task combines existing skills. Treat it as belonging to its primary skill."""



# -----------------------------------------------------------------------------
# 1. Generation
# -----------------------------------------------------------------------------

GENERATE_TAXONOMY_PROMPT = """You are building a taxonomy of task types for an agent.

### Shared rules
""" + SHARED_RULES + """

### Environment
{environment}

### Tasks
{tasks}

### Your task
Create a taxonomy that covers every task in this batch. Apply the shared rules when deciding which tasks belong together and which need separate types.

### Output
Return JSON only:
{{"task_types": [{{"name": "...", "definition": "..."}}]}}"""


# -----------------------------------------------------------------------------
# 2. Update
# -----------------------------------------------------------------------------

UPDATE_TAXONOMY_PROMPT = """You are updating a taxonomy using a new batch of tasks.

### Shared rules
""" + SHARED_RULES + """

### Environment
{environment}

### Current taxonomy
{taxonomy}

### New tasks
{tasks}

### Your task
Update the taxonomy to cover the new tasks while preserving coverage of the tasks it already describes.

- Add a type only when no existing type covers the new task.
- Merge or split existing types according to the shared rules.
- Clarify definitions where needed.
- Keep names and definitions unchanged when no revision is needed.

### Output
Return the complete updated taxonomy as JSON only:
{{"task_types": [{{"name": "...", "definition": "..."}}]}}"""


# -----------------------------------------------------------------------------
# Assignment (fixed taxonomy)
# -----------------------------------------------------------------------------

ASSIGN_TASKS_PROMPT = """Assign each task below to exactly one task type from the taxonomy.

### Environment
{environment}

### Taxonomy
{taxonomy}

### Tasks
{tasks}

### Your task
Use the exact type names and their definitions. Do not create or change types. If a task requires multiple skills, choose its primary skill.

### Output
Answer with JSON only, mapping every task id to the exact name of one task type:
{{"assignments": {{"<id>": "<type name>", ...}}}}"""


# -----------------------------------------------------------------------------
# 3. Review
# -----------------------------------------------------------------------------

REVIEW_ASSIGNMENTS_PROMPT = """You are reviewing a taxonomy after all development tasks have been assigned to its types.

### Shared rules
""" + SHARED_RULES + """

### Environment
{environment}

### Current types and assigned examples
Each type below includes its definition, assignment count, and selected task examples.

{audit}

### Your task
Check whether the assigned examples support each type's definition. Merge or split types according to the shared rules.

- For a merge, explain why the types require the same skill, or which type already covers the other and why no additional instructions are needed.
- For a split, explain which different procedures are currently grouped together and why one does not already cover the other.
- Do not merge a type because it is small or split it because it is large.
- Keep unchanged types' names and definitions.
- If no change is justified, return the taxonomy unchanged.

### Output
Return the complete reviewed taxonomy and decisions as JSON only. Every decision must match the returned taxonomy: merged types must be consolidated, and split types must appear separately.

{{"task_types": [{{"name": "...", "definition": "..."}}],
  "decisions": [{{"action": "keep|merge|split", "sources": ["..."],
                  "target": "...", "reason": "..."}}]}}"""

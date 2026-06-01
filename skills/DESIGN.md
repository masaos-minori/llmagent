# Skill Design Principles

**Essential definition:** A SKILL is a formalized, re-executable encoding of a work procedure.

**Design principles** — every SKILL must satisfy all of these:

| Principle | What it means |
|---|---|
| Write the minimum necessary | Include only what cannot be inferred from the code or context; omit obvious steps |
| Spell out the procedure | List concrete, ordered steps — no ambiguous verbs like "handle" or "deal with" |
| Reduce judgment | Pre-decide branching logic so the executor never has to improvise |
| Define the deliverable | State exactly what artifact or state change marks the SKILL complete |
| Include verification | Provide a concrete check command or assertion that confirms success |
| Compose with other SKILLs | Design so the SKILL can be chained; avoid re-encoding what another SKILL already covers |
| Optimize for token efficiency | Front-load critical rules; cut prose that does not constrain behavior |
| Design to prevent failure | Anticipate common error modes and encode the guard or recovery inline |

**Runtime policy** — every skill execution must load the files listed in `routing.md` (`## Always load alongside the skill`). Do not repeat their content inside SKILL.md files.

**Evaluation criteria** — a SKILL is good when it:

- Runs autonomously end-to-end without human intervention
- Produces the same result on every execution (idempotent)
- Requires no judgment calls from the executor beyond reading the input
- Can be improved incrementally without breaking existing callers
- Contains an `## Improvement feedback` section — after running, update that section when a phase gate was wrong or a recovery path was missing

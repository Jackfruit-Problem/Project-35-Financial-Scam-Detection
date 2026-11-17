# UML Diagrams

Six UML diagrams for Project 35 (FSDIRAS), drawn to match the code in
`backend/app/models` and the routes that actually exist.

| File | Diagram | Covers |
|---|---|---|
| `01_usecase.png` | Use-case | 5 actors, 17 use cases, `<<include>>` / `<<extend>>` — Lab 1 |
| `02_component.png` | Component | 7 components with ball-and-socket interfaces — Lab 3 |
| `03_class.png` | Class | all 15 entities, visibility, multiplicities, composition |
| `04_sequence.png` | Sequence | submitting a scam report, REQ-2 through REQ-8 |
| `05_state.png` | State machine | case lifecycle (REQ-12) and recovery lifecycle (REQ-16) |
| `06_activity.png` | Activity | evidence upload and chain-of-custody hashing |

`FSDIRAS - UML Diagrams.pdf` holds all six, one per page, for submission.

## Regenerating

```
curl -o mermaid.min.js https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js
python gen_uml.py     # writes the HTML sources
python shoot_uml.py   # renders PNGs + the PDF (needs playwright)
```

Figures 1 and 2 are hand-written SVG, because Mermaid has no use-case or
component notation. Figures 3-6 are Mermaid, which does render those four as
real UML.

Note: `../design-diagrams.md` section 1 holds an earlier *flowchart* of the
same use cases. It is not UML notation; Figure 1 here replaces it for anything
that has to be submitted as a UML diagram.

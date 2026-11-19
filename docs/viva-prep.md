# Software Engineering Viva — Preparation Guide

**For:** Mohammed Muaz Iqubal · UE24CS341A · Project 35 (FSDIRAS)

How to use this: part A is the general theory an examiner can ask any SE
student. Part B is your own project — this is where most marks are won or lost,
because answers grounded in a real system are impossible to fake and obviously
yours. Part C is the traps. Read B and C last thing before you go in.

---

# PART A — General software engineering

## A1. The SDLC models

| Model | How it works | Use when | Weakness |
|---|---|---|---|
| **Waterfall** | Requirements → Design → Implementation → Testing → Maintenance, each finished before the next | Requirements are fixed and well understood (compliance, hardware-coupled) | A requirement error found late is catastrophically expensive |
| **V-Model** | Waterfall bent into a V; every development stage has a matching test level | Safety-critical work needing traceable verification | Same rigidity as waterfall |
| **Incremental** | Build and deliver in slices, each adding function | You can usefully ship a partial system | Needs good architecture up front |
| **Iterative** | Build a rough whole, refine it repeatedly | Requirements will be discovered by using it | Can drift without discipline |
| **Spiral** | Iterative + explicit risk analysis each loop | Large, high-risk, expensive projects | Heavyweight, needs risk expertise |
| **Agile** | Short timeboxed iterations, continuous feedback | Requirements will change, customer is available | Needs discipline; weak documentation if done badly |

**Likely question — "which did you use and why?"** Agile/Scrum. The honest reason:
the SRS fixed *what* to build, but the detection threshold could only be settled
by experiment. It landed at 0.17, not the obvious 0.5. A waterfall plan would
have committed to a number before there was any evidence for it.

## A2. Agile

**The four values of the Agile Manifesto** — the left side is valued *more*, not
the right side discarded:

1. Individuals and interactions over processes and tools
2. Working software over comprehensive documentation
3. Customer collaboration over contract negotiation
4. Responding to change over following a plan

**Key principles to be able to name:** deliver working software frequently;
welcome changing requirements even late; business people and developers work
together daily; sustainable pace; technical excellence; simplicity; self-organising
teams; regular reflection and adjustment (that last one is the retrospective).

## A3. Scrum — the framework in full

**Three pillars:** transparency, inspection, adaptation.
**Five values:** commitment, courage, focus, openness, respect.

### Roles (Scrum calls them accountabilities)

| Role | Owns | Does not |
|---|---|---|
| **Product Owner** | The product backlog, its ordering, maximising value | Tell the team *how* to build |
| **Scrum Master** | The process; removes impediments; coaches | Assign tasks; act as a manager |
| **Developers** | The sprint backlog, the increment, the how | Accept work mid-sprint from outside |

### Events (ceremonies)

| Event | Timebox (1-month sprint) | Purpose |
|---|---|---|
| **Sprint** | ≤ 1 month | The container for all other events |
| **Sprint Planning** | 8 h | What can be delivered, and how |
| **Daily Scrum** | 15 min | Developers re-plan the next 24 h. Not a status report to a manager |
| **Sprint Review** | 4 h | Demo the increment to stakeholders, adapt the backlog |
| **Sprint Retrospective** | 3 h | Inspect the *process*; produce actionable improvements |

Timeboxes scale down proportionally for shorter sprints — a 2-week sprint gets
4 h planning, 2 h review, 1.5 h retro.

### Artifacts and their commitments

| Artifact | Commitment |
|---|---|
| Product Backlog | Product Goal |
| Sprint Backlog | Sprint Goal |
| Increment | Definition of Done |

**Definition of Done vs Acceptance Criteria** — a classic question.
*DoD* is one standard applying to **every** item (tests pass, reviewed, linted,
documented). *Acceptance criteria* are specific to **one** story. A story can meet
its acceptance criteria and still not be Done.

## A4. Epic, feature, user story, task

The decomposition hierarchy, largest to smallest:

```
Initiative  →  Epic  →  Feature  →  User Story  →  Task  →  Sub-task
```

- **Epic** — a large body of work spanning multiple sprints, too big to estimate
  reliably. Gets broken down. *Example from your project: "Recovery and Reporting
  Assistance" (REQ-15 to REQ-19).*
- **User story** — the smallest unit of user-visible value, fits in one sprint.
  Format: **As a &lt;role&gt;, I want &lt;goal&gt;, so that &lt;benefit&gt;.**
  *Example: "As a recovery officer, I want to record the amount recovered so that
  the victim can see progress against what they lost."*
- **Task** — a technical step inside a story; hours, not days. Owned by one person.
- **Spike** — a timeboxed research story when you cannot estimate until you learn
  something.

**INVEST** — what makes a good user story: **I**ndependent, **N**egotiable,
**V**aluable, **E**stimable, **S**mall, **T**estable.

**3 Cs of a story:** Card (written), Conversation (discussed), Confirmation
(acceptance criteria).

## A5. Estimation and tracking

- **Story points** — relative size combining complexity, effort and uncertainty.
  Deliberately *not* hours, so estimates do not become commitments about time.
- **Planning poker** — simultaneous reveal, so nobody anchors on the senior voice.
- **Fibonacci (1,2,3,5,8,13)** — gaps widen because large estimates are less precise;
  it stops false arguments between 8 and 9.
- **Velocity** — points completed per sprint, averaged. A *capacity forecast for
  that team*, never a productivity score, and never comparable between teams.
- **Burndown chart** — work remaining vs time; should trend to zero.
  **Burnup** — work completed vs total scope; it also shows scope creep, which a
  burndown hides.
- **Cumulative flow diagram** — band widths show where work piles up (bottlenecks).

## A6. Kanban, Scrum, Scrumban, SAFe

| | Scrum | Kanban |
|---|---|---|
| Cadence | Fixed sprints | Continuous flow |
| Change mid-cycle | Discouraged | Allowed any time |
| Core metric | Velocity | Cycle time, lead time, WIP |
| Roles | Defined | None required |
| Board | Resets each sprint | Persistent |

**WIP limits** are the heart of Kanban: limiting work in progress exposes
bottlenecks and reduces cycle time (Little's Law: *cycle time = WIP ÷ throughput*).
**Scrumban** = Scrum's ceremonies with Kanban's flow and WIP limits.
**SAFe / LeSS** = scaling frameworks for many teams on one product.

## A7. Requirements engineering

**Process:** elicitation → analysis → specification → validation → management.

- **Functional requirement** — what the system *does* ("shall compute a risk score").
- **Non-functional requirement (NFR)** — a quality constraint: performance,
  security, usability, reliability, maintainability, portability, scalability.
  *Your REQ-2 is interesting because it is both — it specifies the behaviour and
  a 5-second / 95% performance bound.*
- **FURPS+** — Functionality, Usability, Reliability, Performance, Supportability,
  plus design/implementation/interface/physical constraints.
- **MoSCoW** prioritisation — Must, Should, Could, Won't (this time).
- **Traceability matrix** — maps each requirement to design, code and test, so you
  can prove coverage and assess the blast radius of a change.
- **Elicitation techniques:** interviews, workshops, questionnaires, observation,
  prototyping, document analysis, use cases.

**A good requirement is:** complete, consistent, unambiguous, verifiable,
traceable, feasible, and necessary.

## A8. UML — all 14 diagrams

Split into **structural** (what the system *is*) and **behavioural** (what it *does*).

**Structural (7):** Class, Object, Component, Deployment, Package, Composite
Structure, Profile.
**Behavioural (7):** Use Case, Activity, State Machine, Sequence, Communication,
Interaction Overview, Timing.

### Class-diagram relationships — a guaranteed question

| Relationship | Notation | Meaning | Test |
|---|---|---|---|
| **Association** | plain line | they know about each other | — |
| **Aggregation** | hollow diamond | "has-a", parts survive the whole | Department–Professor |
| **Composition** | filled diamond | "owns-a", parts die with the whole | Case–Evidence |
| **Inheritance** | hollow triangle arrow | "is-a" | — |
| **Realization** | dashed + hollow triangle | implements an interface | — |
| **Dependency** | dashed arrow | uses temporarily | — |

**Multiplicity:** `1`, `0..1`, `1..*`, `0..*`, `n..m`.
**Visibility:** `+` public, `-` private, `#` protected, `~` package.

### Use-case specifics

Actors (stick figures) sit **outside** the system boundary. `«include»` is
mandatory and always happens; `«extend»` is conditional. Generalization between
actors is a solid triangle arrow.

## A9. Architecture and design

**Architectural patterns:** Layered, Client–Server, MVC/MVVM, Microservices,
Event-Driven, Pipe-and-Filter, Microkernel, Serverless, Broker, Repository.

**Architecture vs design:** architecture is the set of decisions that are
expensive to reverse (how components divide, how they talk); design is what
happens inside a component.

**SOLID**

| | Principle | One line |
|---|---|---|
| **S** | Single Responsibility | one reason to change |
| **O** | Open/Closed | open for extension, closed for modification |
| **L** | Liskov Substitution | a subtype must be usable wherever its base is |
| **I** | Interface Segregation | many small interfaces beat one fat one |
| **D** | Dependency Inversion | depend on abstractions, not concretions |

**Other principles:** DRY, KISS, YAGNI, Separation of Concerns, Law of Demeter.

**Coupling and cohesion** — aim for **low coupling, high cohesion**.
Cohesion best→worst: functional, sequential, communicational, procedural,
temporal, logical, coincidental.
Coupling best→worst: data, stamp, control, external, common, content.

**Design patterns (GoF, 23 in 3 families)**
- *Creational:* Singleton, Factory Method, Abstract Factory, Builder, Prototype
- *Structural:* Adapter, Decorator, Facade, Proxy, Composite, Bridge, Flyweight
- *Behavioural:* Observer, Strategy, Command, State, Template Method, Iterator,
  Mediator, Chain of Responsibility, Visitor, Memento, Interpreter

Know **Singleton, Factory, Observer, Strategy, Adapter, Decorator** cold — those
are the ones asked.

## A10. Testing

**Levels:** Unit → Integration → System → Acceptance (UAT).

**Types:** functional, regression, smoke, sanity, performance/load/stress, security,
usability, compatibility, exploratory.

**Black box vs white box vs grey box.**
- *Black-box techniques:* equivalence partitioning, boundary value analysis,
  decision tables, state transition, pairwise.
- *White-box coverage:* statement → branch/decision → condition → path.
  **Branch coverage is stronger than statement coverage** — `if (a)` with one
  passing test gives 100% statement, 50% branch.

**Test pyramid:** many fast unit tests at the base, fewer integration, fewest
slow end-to-end at the top. The anti-pattern is the "ice-cream cone".

**TDD:** Red → Green → Refactor. **BDD:** Given–When–Then.

**Verification vs validation** — *Verification*: are we building the product
right? (reviews, static analysis). *Validation*: are we building the right
product? (actual execution against need).

**Defect terms:** error (human mistake) → defect/fault (in the artifact) →
failure (observed wrong behaviour). **Severity** = technical impact;
**priority** = fix urgency. They are independent: a typo in the company name on
the landing page is low severity, high priority.

## A11. DevOps, CI/CD, version control

- **CI** — every push merges to a shared branch and is built and tested automatically.
- **CD** — *delivery*: every build is releasable. *Deployment*: every build is
  actually released.
- **Pipeline:** build → test → static analysis → package → deploy → monitor.
- **Branching:** Git Flow (main/develop/feature/release/hotfix), GitHub Flow
  (main + short feature branches), trunk-based (short-lived branches, feature flags).
- **Merge vs rebase:** merge preserves true history; rebase gives a linear one but
  rewrites commits — never rebase a shared branch.
- **Deployment strategies:** blue-green, canary, rolling, feature flags.
- **Infrastructure as Code, containerisation** (Docker image vs container),
  orchestration (Kubernetes).
- **The 12-Factor App** — notably config in the environment, not in code.

## A12. Maintenance, quality, metrics

**Four kinds of maintenance:** corrective (fix defects), adaptive (new
environment), perfective (new features/performance), preventive (refactoring,
reducing future cost). Perfective is typically the largest share.

**Technical debt** — the future cost of a shortcut taken now. Deliberate debt
recorded and scheduled is a legitimate engineering choice; accidental, unrecorded
debt is not.

**Metrics:** LOC (weak), cyclomatic complexity (independent paths = E − N + 2P),
defect density, code coverage, MTTR, lead time, DORA four (deployment frequency,
lead time for changes, change failure rate, time to restore).

**Models:** CMMI levels 1–5 (Initial, Managed, Defined, Quantitatively Managed,
Optimizing); ISO 9126 / 25010 quality characteristics.

**Cost estimation:** COCOMO (Basic/Intermediate/Detailed; Organic, Semi-detached,
Embedded), Function Point Analysis.

## A13. Risk management

Identify → analyse (probability × impact) → plan → monitor.
Responses: **avoid, transfer, mitigate, accept**.
Risk exposure = probability × cost of the loss.

---

# PART B — Your project: FSDIRAS

Have these numbers ready. Precision is what makes an examiner believe you built it.

| Fact | Value |
|---|---|
| Full name | Financial Scam Detection, Investigation and Recovery Assistance System |
| Course / ID | UE24CS341A, Project 35, team Sentinel Squad |
| Requirements | 25 functional, REQ-1 to REQ-25, all implemented |
| Your module | **Recovery & Reporting Assistance, REQ-15 to REQ-19** |
| Architecture | Layered client–server; ML isolated as its own service |
| Stack | FastAPI + React/TypeScript + PostgreSQL (SQLite fallback), scikit-learn |
| Scale | 15 tables, 40 API endpoints, 9 screens |
| Tests | 167 automated (130 backend + 37 ML), all passing |
| Model | TF-IDF (word 1-2, char 3-5) → logistic regression |
| Model quality | precision 0.950, recall 0.993, AUC 0.9994; threshold **0.17** |
| Roles | Guest, Victim, Investigator, Recovery Officer, Administrator |

### The five questions you will almost certainly get

**1. "Explain your architecture and why."**
Layered client–server. React SPA → FastAPI → PostgreSQL, with the ML model
deliberately behind its own HTTP boundary on port 8001. That separation means the
model can be retrained, versioned or taken down without the API losing the ability
to score — it falls back to a rule-based scorer. It also lets the model scale
independently, since scoring is the CPU-heavy part.

**2. "Why threshold 0.17 and not 0.5?"**
Because the costs are asymmetric. Telling a victim a scam is safe (false negative)
is far worse than flagging a safe message for review (false positive). 0.17 is the
lowest threshold that still holds precision at 95%, which maximises recall under
that constraint. The 0–100 score is anchored so that the threshold maps exactly to
70, the bottom of the High band.

**3. "What was the hardest bug?"**
The chain-of-custody hash mismatch. SQLite returns naive datetimes and PostgreSQL
returns timezone-aware ones. Hashing `datetime.isoformat()` therefore produced a
different digest on write than on read, and every custody chain failed verification.
Fixed by passing every timestamp through `canonical_ts()` — naive UTC, microsecond
precision — before hashing. The lasting lesson: **the field order in
`compute_entry_hash` is part of the data format; reordering it invalidates every
chain ever written.**

**4. "How do you guarantee evidence is not tampered with?" (your REQ-11/13)**
Append-only hash chain. Each custody event stores `prev_hash` and its own
`entry_hash` computed over the previous hash plus its own fields. Altering any
historical row breaks every subsequent hash, and `verify_chain` detects it.
Evidence can never be deleted, only archived with a recorded reason. An ORM rule
saying "don't delete" would not be defensible — it is enforced by the data
structure, not by politeness.

**5. "Walk me through what happens when a user submits a report."**
Validate against Appendix B → check the blacklist first (cheap, exact) → if no
match, call the ML service → anchor the probability to 0–100 and band it → insert
the report and a detection log → open a case with a generated Case ID → allocate
the least-loaded active investigator → queue a notification → return the Case ID.
*This is Figure 4, your sequence diagram.*

### Your own module, in depth (REQ-15 to REQ-19)

- **REQ-15** auto-populates the recovery request from data already in the case, so
  a traumatised victim does not retype it.
- **REQ-16** five statuses: Requested, In Progress, Partially Recovered, Fully
  Recovered, Rejected.
- **REQ-17** PDF case report via reportlab.
- **REQ-18** notification to the victim on every status change.
- **REQ-19** amount reported vs amount recovered.

**Know this defect — it shows judgement.** Recovery could never be recorded when no
loss amount was stated. The SRS makes the amount optional, 0 meant "not stated",
and the ceiling check compared the recovered figure against it — so 0 capped
everything at 0. The fix: apply the ceiling only when the reported amount is
greater than 0, and otherwise treat the recovered figure as the reported one.

### Process questions about your project

- **Sprints:** two. Sprint 1 (6–7 Sep) implemented all four modules; Sprint 2
  (28 Sep – 29 Oct) added the ML service and hardening.
- **Biggest process lesson:** a test that cannot fail is not evidence. Five tests
  were passing against their own stub and asserting nothing; an audit of the
  finished system found seven real defects the 93-test suite had missed. Every one
  now has a regression test.
- **Technical debt we recorded and then paid:** `create_all` was never a migration
  path, because it cannot alter an existing table. It has been replaced with
  Alembic migrations, plus tests asserting the migrations produce exactly the
  schema the models declare.

---

# PART C — Traps and rapid-fire

### Trap questions

**"Is Agile better than Waterfall?"**
No — it depends. Waterfall is right when requirements are genuinely fixed and
verification must be traceable, like avionics. Saying "Agile is always better" is
the wrong answer.

**"Your use-case diagram shows Victim uploading evidence. Can a victim upload to
any case?"**
No. Use-case notation cannot express ownership, so it is stated as a note and
enforced in code: a victim reaches evidence only for their own case, an
investigator only for a case assigned to them, and there are tests that call each
endpoint as the wrong role and require a refusal.

**"You have 167 passing tests. Does that mean there are no bugs?"**
No. Testing shows the presence of defects, never their absence (Dijkstra). Our own
audit proved it — seven real defects while the suite was green.

**"Why not just use 100% code coverage as the quality bar?"**
Coverage measures which lines ran, not whether anything was asserted about them.
Five of our tests had 100% coverage of code they verified nothing about.

**"What is the difference between a sprint and an iteration?"**
Effectively the same concept; "sprint" is Scrum's term. A sprint is strictly
timeboxed and ends with a potentially shippable increment.

**"Who writes user stories?"**
The Product Owner is accountable for the backlog, but anyone can write a story;
it is refined collaboratively.

**"Can a sprint be extended if work is unfinished?"**
No. The timebox is fixed. Unfinished work returns to the product backlog and is
re-estimated. Only the Product Owner can cancel a sprint.

### Rapid-fire one-liners

| Question | Answer |
|---|---|
| Coupling vs cohesion | Low coupling between modules, high cohesion within one |
| Verification vs validation | Right product vs product right |
| Severity vs priority | Technical impact vs fix urgency |
| Regression vs retesting | Check nothing else broke vs confirm this fix works |
| Smoke vs sanity | Build is stable enough to test vs narrow check after a small change |
| Alpha vs beta | In-house vs real users |
| Error/defect/failure | Human mistake → in the artifact → observed behaviour |
| Epic vs story | Multi-sprint, decomposed vs one sprint, user-visible value |
| DoD vs acceptance criteria | Applies to all items vs specific to one story |
| Velocity | Points per sprint; a forecast, never a performance score |
| Burndown vs burnup | Remaining vs completed; burnup also shows scope change |
| CI vs CD | Integrate and test on every push vs always releasable/released |
| Monolith vs microservices | One deployable vs independently deployable services |
| SOAP vs REST | Protocol with strict contract vs architectural style over HTTP |
| Authentication vs authorization | Who you are vs what you may do |
| Stateless | Server keeps no session between requests — why JWT scales |
| Normalisation | Remove redundancy; 1NF atomic, 2NF no partial dependency, 3NF no transitive |
| ACID | Atomicity, Consistency, Isolation, Durability |
| Idempotent | Same result however many times it runs (GET, PUT, DELETE) |
| Cyclomatic complexity | E − N + 2P; independent paths through the code |
| Technical debt | Future cost of a shortcut taken now |
| Refactoring | Change structure, never behaviour |
| Code smell | Symptom suggesting a deeper design problem |
| Pair programming | Two people, one keyboard; review happens as you write |
| Scrum of Scrums | Representatives coordinate across multiple Scrum teams |
| Spike | Timeboxed research when you cannot yet estimate |
| Definition of Ready | Criteria a story must meet before entering a sprint |
| Three amigos | BD + dev + tester agree a story before building it |

### The last thing to remember

If you do not know something, say so and then reason from a principle rather than
bluffing. "I haven't used Kubernetes, but the problem it solves is orchestrating
many containers — scheduling, scaling and restarting them — which is the same role
Docker Compose plays for us on one machine" earns far more than a confident wrong
answer.

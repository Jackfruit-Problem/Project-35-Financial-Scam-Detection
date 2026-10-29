# Sprint Retrospective — Facilitator Checklist

Project ID 35 · UE24CS341A · Team Sentinel Squad

Copy this file for each sprint, fill in the header, and work down the checklist.
Everything in it is meant to be edited: the Status column, the action items, and
the timings.

---

## Session details

| Field | Value |
|---|---|
| Sprint number | |
| Date | |
| Facilitator (Scrum Master) | |
| Attendees | |
| Absent / notes | |
| Framework chosen | *e.g. Start-Stop-Continue, 4Ls, Sailboat* |

### Timebox

| | Minutes |
|---|---|
| Phases 1 and 7 — done **outside** the meeting | 30 |
| Phases 2 to 6 — the meeting itself | **85** |
| Total effort | 115 |

Worth knowing before booking a room: adding up every row below gives 115
minutes, but preparation and follow-through happen before and after, so the
session you actually schedule is **85 minutes**. With four people rather than a
large team, the brainstorming and voting rows usually finish early — take the
time back rather than filling it.

---

## The Retrospective Prime Directive

Read aloud at the start of phase 2, before anything else is discussed.

> "Regardless of what we discover, we understand and truly believe that
> everyone did the best job they could, given what they knew at the time,
> their skills and abilities, the resources available, and the situation at
> hand."
>
> — Norman Kerth, *Project Retrospectives: A Handbook for Team Reviews*

The point of reading it out is not ceremony. A retrospective that turns into an
argument about who caused a problem produces no action items, and the next one
is attended reluctantly. Saying this first makes it easier to raise the awkward
thing, which is the only reason the meeting exists.

---

## Checklist

Status values: `Not Started` · `In Progress` · `Done` · `Skipped (reason)`

### 1. Preparation — before the session · 20 mins

| Activity | Purpose and guidance | Time | Status |
|---|---|---|---|
| Review previous action items | Check the status of commitments made last sprint. Carry anything unfinished into this session — an action item that silently disappears teaches the team that these meetings do not matter. | 5 mins | Not Started |
| Gather objective metrics | Pull sprint velocity, burndown/burnup, escaped defects, and completed vs. planned story points. Bring numbers so the discussion argues with data rather than with memory. | 5 mins | Not Started |
| Select retro framework | Choose a structure matching the team's current state (Start/Stop/Continue, 4Ls, Sailboat) and prepare the boards in advance. | 5 mins | Not Started |
| Set a safe environment | If the sprint involved conflict or anything sensitive, send an anonymous feedback form beforehand so quieter views reach the session at all. | 5 mins | Not Started |

### 2. Set the stage · 10 mins

| Activity | Purpose and guidance | Time | Status |
|---|---|---|---|
| Welcome and safety check | Read the Prime Directive above. Run an anonymous 1–5 safety poll to gauge how openly people feel able to speak. If the average is low, say so and shorten the session rather than pressing on. | 5 mins | Not Started |
| Icebreaker | A short non-work check-in to move attention away from whatever everyone was doing five minutes ago. | 5 mins | Not Started |

### 3. Gather data · 20 mins

| Activity | Purpose and guidance | Time | Status |
|---|---|---|---|
| Brainstorming | Each person adds notes **silently** on what went well, what did not, and what could improve. Silent writing first stops the loudest or most senior voice from setting the agenda. | 10 mins | Not Started |
| Review sprint timeline | Reconstruct the sprint in order, marking emotional peaks, technical blockers and scope changes. Memory of a two-week sprint is mostly the last two days; the timeline corrects that. | 10 mins | Not Started |

### 4. Generate insights · 25 mins

| Activity | Purpose and guidance | Time | Status |
|---|---|---|---|
| Affinity mapping | Group the notes into themes — technical debt, communication, scope creep, and so on. | 10 mins | Not Started |
| Root cause analysis | Apply *5 Whys* or a Fishbone diagram to the highest-priority themes. Treat causes, not symptoms: "the build broke" is a symptom; "nobody runs the tests before pushing" is a cause you can act on. | 15 mins | Not Started |

### 5. Decide actions · 20 mins

| Activity | Purpose and guidance | Time | Status |
|---|---|---|---|
| Dot voting | Give everyone a fixed number of dots to prioritise which themes get acted on. Fixed tokens force a choice; open discussion does not. | 5 mins | Not Started |
| Define SMART action items | Convert the top problems into **one or two** specific, measurable actions. Record them in the table below. Exactly one owner each. | 15 mins | Not Started |

**Why one or two, not five.** A retrospective that produces eight action items
produces none: nothing has capacity, nothing has an owner who feels responsible,
and next sprint opens by reviewing eight failures. Two actions that actually
land beat eight that are listed.

### 6. Close the session · 10 mins

| Activity | Purpose and guidance | Time | Status |
|---|---|---|---|
| Summarise commitments | Read the action items, owners and validation criteria out loud. People disagree about what was decided far more often than they realise; reading it back catches it while everyone is still in the room. | 5 mins | Not Started |
| Feedback on the retro (ROTI) | Run a Return on Time Invested poll and record it below. The retrospective is itself a process that can be improved. | 5 mins | Not Started |

### 7. Follow-through — after the session · 10 mins

| Activity | Purpose and guidance | Time | Status |
|---|---|---|---|
| Integrate into the sprint backlog | Move the agreed actions into the upcoming Sprint Backlog with real capacity allocated. An action item outside the backlog is a wish. | 5 mins | Not Started |
| Publish and archive | Commit the completed copy of this file to `docs/` so the next retrospective can start by reviewing it. | 5 mins | Not Started |

---

## Action items from this sprint

One owner each. "How we will know it worked" is the part that stops an action
item from being quietly declared done.

| # | Action | Owner | Due | How we will know it worked | Status |
|---|---|---|---|---|---|
| 1 | | | | | Not Started |
| 2 | | | | | Not Started |

### Carried over from the previous sprint

| # | Action | Owner | Originally due | Why it did not land | Status |
|---|---|---|---|---|---|
| | | | | | |

---

## ROTI result

Each person rates the hour: 1 = wasted, 5 = very valuable.

| Rating | Votes |
|---|---|
| 5 — very valuable | |
| 4 — useful | |
| 3 — about break-even | |
| 2 — some value | |
| 1 — wasted time | |

**Average:**

**Anything a 1 or 2 voter wants changed next time:**

---

## Sprint metrics

Filled during phase 1 and kept with the retrospective so trends are visible
across sprints.

| Metric | This sprint | Previous sprint |
|---|---|---|
| Story points planned | | |
| Story points completed | | |
| Velocity | | |
| Escaped defects | | |
| Automated tests passing | | |
| Requirements complete (of 25) | | |

---

## Notes

- Keep one completed copy per sprint in `docs/`, named
  `retrospective-sprint-<n>.md`. This file stays as the blank template.
- If an action item is carried over twice, it is not an action item. Either
  drop it or break it into something small enough to finish.

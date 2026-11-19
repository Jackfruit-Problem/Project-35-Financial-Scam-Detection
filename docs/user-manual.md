# User Manual

FSDIRAS — Financial Scam Detection, Investigation and Recovery Assistance System
Project ID 35 · UE24CS341A · Team Sentinel Squad · version 1.0, 19 November 2026

| | |
|---|---|
| Audience | Members of the public, investigators, recovery officers and administrators |
| Covers | All nine screens of the web application |
| Does not cover | Installing and running the system — that is `RUNNING.md`; hosting it — that is `deployment.md` |

---

## 1. What the system does

FSDIRAS does four things, and it is worth being clear about the boundary of
each:

1. **Screens a suspicious message** and gives it a risk score out of 100 with
   the reasons behind it.
2. **Takes a scam report** from a victim, opens a case with a reference, and
   puts it in front of an investigator.
3. **Holds evidence** so that nobody — including an administrator — can alter
   or delete it without the system being able to prove it.
4. **Tracks a recovery attempt** and produces printable PDF reports to hand to
   a bank, the police or the RBI Ombudsman.

**What it is not.** The risk score is advisory. The system does not decide that
something is a scam, does not contact your bank, and does not recover money by
itself. It organises the evidence and the paperwork that a human process needs.

---

## 2. Signing in

Open the application in a browser (`http://localhost:5173` when it is running
locally). Three screens work without an account at all: the home page,
**Check a message**, and **Learn to spot a scam**.

### Demo accounts

Every demo account uses the password `password123`.

| Role | E-mail | What it can do |
|---|---|---|
| Victim | `victim@fsdiras.example.com` | File reports, upload evidence to their own case, download their own PDF |
| Victim | `victim2@fsdiras.example.com` | A second victim — useful for showing that one victim cannot see another's case |
| Investigator | `investigator@fsdiras.example.com` | Work the cases assigned to them |
| Investigator | `investigator2@fsdiras.example.com` | A second investigator — shows how allocation spreads load |
| Recovery officer | `officer@fsdiras.example.com` | Raise and update recovery requests |
| Administrator | `admin@fsdiras.example.com` | Users, roles, blacklist, analytics, model |

The sign-in screen lists these accounts, so there is nothing to memorise during
a demonstration.

To create a real account, use **Sign in → register**. A new account is always a
victim: a role cannot be self-assigned, and only an administrator can change
one.

### Roles at a glance

| Role | Sees | Cannot |
|---|---|---|
| Guest (not signed in) | Home, Check a message, Awareness | File a report, see any case |
| Victim | Their own reports, their own cases, their own evidence, their own PDF | See anyone else's anything; archive evidence; set a recovery outcome |
| Investigator | The queue of cases assigned to them, with full case detail | See cases assigned to someone else; record a recovery outcome |
| Recovery officer | Cases and their recovery records | Change a case's investigation status |
| Administrator | Everything, plus users, blacklist, analytics and the model | Delete evidence (no such function exists for anyone) |

---

## 3. For a member of the public

### 3.1 Check a message — no account needed

Screen: **Check a message**

1. Paste the suspicious SMS, WhatsApp message or e-mail into the box.
2. Press **Check**.
3. You get back:
   * a score from 0 to 100,
   * a band — **Low**, **Medium** or **High**,
   * the specific wording that drove the score, under *Result*,
   * a notice that the score is advisory.

If the score worries you, press **Report this as a scam** — it carries the text
straight into the report form, so you do not retype it.

**How to read the bands**

| Band | Score | What it means |
|---|---|---|
| Low | 0 – 39 | Nothing in the message matched known fraud patterns. Not a guarantee. |
| Medium | 40 – 69 | Some signals matched. Treat links and payment requests with suspicion. |
| High | 70 – 100 | The message looks like the fraud the model was trained on, or it contains an identifier already recorded as fraudulent. Do not pay, do not click, do not share an OTP. |

A score of exactly 100 means the message contained a URL, phone number or UPI
ID that is already on the blacklist. That is a recorded fact, not a prediction,
and it skips the model entirely.

### 3.2 Learn to spot a scam

Screen: **Learn to spot a scam**

Awareness articles, filterable by category, and short quizzes. Pick a quiz,
answer it, and submit: it is scored on the server and comes back with an
explanation for each question. The answer key never reaches the browser, so the
answers cannot be found by inspecting the page.

### 3.3 Report a scam

Screen: **Report a scam** (requires an account)

A three-step form. Each step validates before it lets you continue.

| Step | Asks for |
|---|---|
| 1 — Your details | Your name, and a phone number or e-mail to reach you on |
| 2 — What happened | Category (phishing, UPI fraud, loan app, investment, other), a description of what happened, and the amount lost (optional) |
| 3 — Review | Everything you entered, for a last check before submitting |

On submit you land on **Report received**, which shows:

* your **report reference** and **case reference** — 12 characters, e.g.
  `RPT2611X7K2Q`. Quote the case reference in any follow-up.
* the risk score and, under *Why it was scored this way*, the reasons.
* **Open the case and add evidence**, and **View my reports**.

Every report opens a case, whatever the score. A High-risk report is assigned to
an investigator immediately; a lower-risk one waits for a human to pick it up.

### 3.4 Attach evidence

From your case: choose a file and upload it.

| Rule | Value |
|---|---|
| Maximum size | 10 MB |
| Accepted types | PNG, JPEG, WebP, PDF, plain text |
| Scanned before storage | Yes |
| Encrypted on disk | Yes, AES-256-GCM |
| Can be deleted later | **No** — see §6 |

Screenshots of the message, the payment confirmation, and the bank statement
line are the three most useful things to attach.

### 3.5 Follow your case and get the paperwork

Screen: **My reports** — every report you have filed, its case reference, its
status and the risk band.

Open a case to see the investigator's notes, the evidence and the recovery
record. **Download the case report** gives you a PDF that carries the case
reference and the legal disclaimer on every page: that is the document to take
to a bank or a police station.

---

## 4. For an investigator

Screen: **My case queue** → open a case → **Case detail**

The queue shows only the cases assigned to you. That is enforced on the server,
not hidden in the interface.

A case detail screen has five sections:

1. **The report** — what the victim submitted, the risk score and the reasons.
2. **Evidence** — every file, with **Verify** and **Archive**.
3. **Investigation notes** — add a note; it is stamped with your name and the
   time, and neither can be edited afterwards.
4. **Update status** — one of exactly five values, with an optional note
   explaining the change:
   `new → under_investigation → escalated → resolved → closed`.
   Only the assigned investigator can change the status of a case.
5. **Recovery** — visible here, but only a recovery officer can write to it.

### Verifying evidence

**Verify** recomputes the whole chain of custody for that file and answers one
question: has anything in this item's history been altered?

* **Intact** — every link's hash matches. The file and its history are as
  recorded.
* **Broken at entry N** — something was changed, reordered or deleted at that
  point. Everything after it is suspect.

This is the function to demonstrate if anyone asks how the system proves its
evidence has not been tampered with. Uploading, viewing, downloading and
archiving each add a link to the chain, so the history also shows **who looked
at the file and when**.

### Archiving

Evidence can be archived with a reason. It cannot be deleted — by anyone.
Archived evidence stays in the chain of custody and remains verifiable.

---

## 5. For a recovery officer

Screen: **Case detail → Recovery**

1. **Raise recovery request.** Fill in the bank name (e.g. *State Bank of
   India*) and the IFSC (e.g. *SBIN0001234*). Everything else — the victim, the
   case, the amount reported lost — is filled in from the case. One recovery
   request per case.
2. **Update recovery.** Set the status and the amount actually recovered:
   `requested → in_progress → partially_recovered → fully_recovered`, or
   `rejected`.
   * The recovered amount cannot exceed the reported loss. The server refuses
     it, not the form.
   * Every status change writes a notification to the victim. If the e-mail or
     SMS gateway is down, the notification is still recorded — it is never
     silently lost.
3. **Download the recovery report.** A PDF stating what was lost, what came
   back, and where it stands — with the disclaimer on every page.

An investigator cannot record a recovery outcome, and a victim cannot raise a
recovery request. Both are enforced on the server.

---

## 6. For an administrator

Screen: **Administration**

| Section | What you can do |
|---|---|
| Money / analytics | Totals by case status, trending scam categories, reported versus recovered amounts |
| Users and roles | Change any account's role; deactivate an account |
| Blacklisted identifiers | Add a URL, phone number or UPI ID (e.g. `fraudster@ybl`) with a reason such as *Reported in 12 cases*; remove an entry |
| Detection model | See §6.2 |

Two guards worth knowing before a demonstration:

* **The last administrator cannot be deactivated.** The system refuses, so
  nobody can lock everyone out.
* **Deactivation takes effect immediately**, including for an account that is
  already signed in with a valid token.

### 6.1 The blacklist is stronger than the model

Anything you add here scores 100 on sight and never reaches the model. Values
are normalised on entry, so `Fraudster@YBL` and `fraudster@ybl` are the same
entry, and a duplicate is refused.

### 6.2 The Detection model tab

Six panels, all served from the model artefact actually in service rather than
typed into the interface:

| Panel | Shows |
|---|---|
| What is running | Model version, algorithm, decision threshold |
| How it scored, by data source | Precision, recall, F1 and ROC-AUC, broken out per data source |
| Why this model | Why a linear model was chosen over a stronger one |
| Stability | Cross-validation mean and spread |
| Known limitations | Stated by the artefact itself, including that half the training data is synthetic |
| Where it was right and wrong | The confusion matrix |

If the model service is not running, this tab says so plainly — *"the detection
model service is not reachable; risk scoring is falling back to the built-in
rules"* — and the rest of the application keeps working. That is the designed
behaviour, not a failure.

---

## 7. Troubleshooting

| What you see | What it means | What to do |
|---|---|---|
| *Too many attempts* on sign-in (429) | Ten wrong passwords for that e-mail address | Wait five minutes. It clears by itself, and it is per address |
| *Invalid credentials* for an address you are sure exists | Wrong password and unknown e-mail give the same message on purpose, so the system cannot be used to discover which addresses are registered | Check the password; use a demo account |
| *File exceeds the 10 MB limit* | The upload is too large | Screenshot the relevant part rather than attaching a video |
| *Unsupported file type* | Only PNG, JPEG, WebP, PDF and plain text are accepted | Convert it, or screenshot it |
| A banner saying the model is unavailable | The model service is not running | Scores still work, from the built-in rules. Start the model service to restore model scoring |
| *Registration refused — invalid e-mail domain* | The address used a non-routable domain such as `.local` or `.test` | Use a normal domain; the demo accounts use `fsdiras.example.com` |
| The case list looks truncated | List endpoints return at most 500 rows, 100 by default | Use the filters; this is a deliberate ceiling, not a bug |
| *Evidence file is missing* | The custody record exists but the file behind it does not | Reported explicitly rather than as a crash, because for evidence specifically "it is gone" must never be mistaken for "something broke" |

---

## 8. Privacy, retention and limits

* **Evidence is encrypted at rest** and cannot be deleted through the
  application by any role. Archiving is the only removal from view, and it
  keeps the file and its history.
* **Every look at an evidence file is recorded** in that item's chain of
  custody, with who and when.
* **Logins, evidence access and status changes are written to an audit log.**
* **The risk score is advisory.** A scam determination requires human review —
  the interface says so on every score, and the PDFs carry the disclaimer on
  every page.
* **Notifications are recorded, and in this version dispatched to the
  application log** rather than to a real e-mail or SMS gateway. The victim sees
  them in the system.
* **The model has stated limitations**, including that the Indian
  financial-fraud half of its training data is synthetic, so live accuracy will
  be lower than the measured figures. The Model tab shows this to any
  administrator who asks.

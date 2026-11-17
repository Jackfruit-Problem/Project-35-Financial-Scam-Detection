# -*- coding: utf-8 -*-
"""UML diagrams for FSDIRAS (Project 35, UE24CS341A).

Use-case and component diagrams are hand-drawn SVG in proper UML notation
(stick-figure actors, system boundary, <<include>>/<<extend>>, ball-and-socket
interfaces). Class / sequence / state / activity use Mermaid, which renders
real UML for those four. Content matches the code in backend/app/models and
the routes that exist, not an idealised design.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

TITLE = "FSDIRAS — Financial Scam Detection, Investigation & Recovery Assistance System"
SUB = "Project ID 35  ·  UE24CS341A Software Engineering  ·  Team Sentinel Squad"

INK = "#1a1a1a"
LINE = "#394150"
ACTOR = "#1f5fbf"
BOUND = "#8a93a5"
FILL = "#eaf1fd"
STER = "#6b7384"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, s, size=15, fill=INK, anchor="start", weight="400", style=""):
    st = ' font-style="italic"' if style else ""
    return ('<text x="%s" y="%s" font-family="Segoe UI, Arial, sans-serif" font-size="%s" '
            'font-weight="%s" fill="%s" text-anchor="%s"%s>%s</text>'
            % (x, y, size, weight, fill, anchor, st, esc(s)))


def rect(x, y, w, h, fill="none", rx=0, stroke=LINE, sw=1.6, dash=""):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" '
            'stroke-width="%s"%s/>' % (x, y, w, h, rx, fill, stroke, sw, d))


def ellipse(cx, cy, rx, ry, fill=FILL, stroke=ACTOR, sw=1.6):
    return ('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" '
            'stroke-width="%s"/>' % (cx, cy, rx, ry, fill, stroke, sw))


def line(x1, y1, x2, y2, stroke=LINE, sw=1.3, dash="", marker=""):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    m = ' marker-end="url(#%s)"' % marker if marker else ""
    return ('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s%s/>'
            % (x1, y1, x2, y2, stroke, sw, d, m))


def stick(cx, cy, label, sub=""):
    """UML actor: stick figure with the name beneath."""
    g = ['<g stroke="%s" stroke-width="2.4" fill="none" stroke-linecap="round">' % ACTOR,
         '<circle cx="%s" cy="%s" r="15" fill="#fff"/>' % (cx, cy - 40),
         '<line x1="%s" y1="%s" x2="%s" y2="%s"/>' % (cx, cy - 25, cx, cy + 16),
         '<line x1="%s" y1="%s" x2="%s" y2="%s"/>' % (cx - 24, cy - 8, cx + 24, cy - 8),
         '<line x1="%s" y1="%s" x2="%s" y2="%s"/>' % (cx, cy + 16, cx - 18, cy + 46),
         '<line x1="%s" y1="%s" x2="%s" y2="%s"/>' % (cx, cy + 16, cx + 18, cy + 46),
         '</g>',
         txt(cx, cy + 70, label, 16, INK, "middle", "700")]
    if sub:
        g.append(txt(cx, cy + 89, sub, 12, STER, "middle"))
    return "".join(g)


DEFS = ('<defs>'
        '<marker id="arrow" viewBox="0 0 10 10" refX="9.5" refY="5" markerWidth="9" '
        'markerHeight="9" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="%s"/></marker>'
        '<marker id="open" viewBox="0 0 10 10" refX="9.5" refY="5" markerWidth="11" '
        'markerHeight="11" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="%s" stroke-width="1.6"/></marker>'
        '</defs>' % (LINE, LINE))


def page(w, h, body, fig, name):
    head = (txt(w / 2, 52, fig, 26, INK, "middle", "700")
            + txt(w / 2, 82, TITLE, 15, "#444", "middle")
            + txt(w / 2, 104, SUB, 13, STER, "middle"))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">'
            '%s<rect width="%s" height="%s" fill="#ffffff"/>%s%s</svg>'
            % (w, h, w, h, DEFS, w, h, head, body))


def html(svg):
    return ('<!doctype html><html><head><meta charset="utf-8"><style>'
            'html,body{margin:0;padding:0;background:#fff}svg{display:block}'
            '</style></head><body>%s</body></html>' % svg)


# ======================================================================= 1
def use_case():
    W, H = 2180, 2010
    g = []
    BX, BY, BW, BH = 600, 150, 1140, 1590
    g.append(rect(BX, BY, BW, BH, "#fcfdff", 6, BOUND, 2))
    g.append(txt(BX + BW / 2, BY + 36, "FSDIRAS", 19, "#3c4455", "middle", "700"))
    g.append(txt(BX + BW / 2, BY + 58, "«system»", 13, STER, "middle", "400", "i"))

    cx, rx, ry = 940, 182, 31
    rows = [
        ("UC12", "Read awareness articles"),
        ("UC13", "Take awareness quiz"),
        ("UC1", "Analyse a message"),
        ("UC2", "Submit scam report"),
        ("UC4", "Upload evidence"),
        ("UC11", "Download case / recovery PDF"),
        ("UC3", "View assigned cases"),
        ("UC5", "Verify chain of custody"),
        ("UC6", "Update case status"),
        ("UC7", "Add case notes"),
        ("UC8", "Archive evidence"),
        ("UC9", "Raise recovery request"),
        ("UC10", "Update recovery status"),
        ("UC14", "Manage users and roles"),
        ("UC15", "Manage blacklist"),
        ("UC16", "Manage awareness content"),
        ("UC17", "View analytics and model metrics"),
    ]
    y0, step = 248, 86
    pos = {}
    for i, (uid, label) in enumerate(rows):
        y = y0 + i * step
        pos[uid] = y
        g.append(ellipse(cx, y, rx, ry))
        g.append(txt(cx, y + 5, label, 14.5, INK, "middle"))

    # included / extended use cases, drawn in their own column
    icx, irx = 1560, 128
    inc = [("UCA", "Create investigation case", pos["UC2"]),
           ("UCB", "Record custody event", pos["UC4"]),
           ("UCC", "Notify victim", pos["UC10"])]
    for uid, label, y in inc:
        g.append(ellipse(icx, y, irx, ry, "#f3f6fb", "#7d879b"))
        g.append(txt(icx, y + 5, label, 13.5, "#333", "middle"))
        pos[uid] = y

    def assoc(ax, ay, uid, left=True):
        ex = cx - rx if left else cx + rx
        return line(ax, ay, ex, pos[uid])

    # ---- actors
    la = 330
    guest_y = pos["UC12"] + 40
    victim_y = (pos["UC1"] + pos["UC11"]) / 2
    inv_y = (pos["UC3"] + pos["UC9"]) / 2
    g.append(stick(la, guest_y, "Guest", "unauthenticated"))
    g.append(stick(la, victim_y, "Victim"))
    g.append(stick(la, inv_y, "Investigator"))

    ra = 1960
    off_y = (pos["UC9"] + pos["UC11"]) / 2 + 120
    adm_y = (pos["UC14"] + pos["UC17"]) / 2
    g.append(stick(ra, off_y, "Recovery Officer"))
    g.append(stick(ra, adm_y, "Administrator"))

    for uid in ("UC12", "UC13"):
        g.append(assoc(la + 30, guest_y, uid))
    for uid in ("UC1", "UC2", "UC4", "UC11", "UC12", "UC13"):
        g.append(assoc(la + 30, victim_y, uid))
    for uid in ("UC1", "UC3", "UC4", "UC5", "UC6", "UC7", "UC8", "UC9", "UC11"):
        g.append(assoc(la + 30, inv_y, uid))
    for uid in ("UC3", "UC9", "UC10", "UC11"):
        g.append(assoc(ra - 30, off_y, uid, left=False))
    for uid in ("UC14", "UC15", "UC16", "UC17"):
        g.append(assoc(ra - 30, adm_y, uid, left=False))

    # ---- include / extend
    def stereo(x1, y1, x2, y2, word, dy=-10):
        s = [line(x1, y1, x2, y2, LINE, 1.4, "7 5", "open"),
             txt((x1 + x2) / 2, (y1 + y2) / 2 + dy, "«%s»" % word,
                 12.5, STER, "middle", "400", "i")]
        return "".join(s)

    g.append(stereo(cx + rx, pos["UC2"], icx - irx, pos["UCA"], "include"))
    g.append(stereo(cx + rx, pos["UC4"], icx - irx, pos["UCB"], "include"))
    g.append(stereo(icx - irx, pos["UCC"], cx + rx, pos["UC10"], "extend"))
    # detection is re-used by report submission
    g.append(stereo(cx - rx - 6, pos["UC2"] - 10, cx - rx - 6, pos["UC1"] + 14, "include", 0))

    # ---- legend
    lx, ly = 160, H - 150
    g.append(rect(lx, ly, 900, 112, "#f7f9fc", 8, "#cfd8e4", 1.4))
    g.append(txt(lx + 18, ly + 28, "Notation", 15, INK, "start", "700"))
    g.append(line(lx + 20, ly + 52, lx + 80, ly + 52))
    g.append(txt(lx + 92, ly + 57, "association (actor takes part in the use case)", 13, "#333"))
    g.append(line(lx + 20, ly + 84, lx + 80, ly + 84, LINE, 1.4, "7 5", "open"))
    g.append(txt(lx + 92, ly + 89,
                 "«include» always runs as part of it  ·  "
                 "«extend» runs only under a condition", 13, "#333"))

    note = ("Ownership is not expressible in the notation and is enforced in code: a Victim reaches "
            "UC4 / UC11 only for their own case, an Investigator only for a case assigned to them.")
    g.append(txt(1100, H - 150 + 57, note, 13, "#555"))
    g.append(txt(1100, H - 150 + 80,
                 "UC10 belongs to the Recovery Officer and Administrator, never the Investigator.",
                 13, "#555"))
    return page(W, H, "".join(g), "Figure 1 — Use-Case Diagram", "usecase")


# ======================================================================= 2
def component():
    W, H = 2100, 1280
    g = []

    def comp(x, y, w, h, name, stereo="component", fill="#eef3fb", note=""):
        s = [rect(x, y, w, h, fill, 4, "#33415c", 1.8),
             # UML component icon
             rect(x + w - 42, y + 12, 26, 18, "#fff", 0, "#33415c", 1.4),
             rect(x + w - 48, y + 15, 12, 5, "#fff", 0, "#33415c", 1.4),
             rect(x + w - 48, y + 23, 12, 5, "#fff", 0, "#33415c", 1.4),
             txt(x + 16, y + 26, "«%s»" % stereo, 12.5, STER, "start", "400", "i"),
             txt(x + 16, y + 50, name, 16, INK, "start", "700")]
        if note:
            for i, ln in enumerate(note.split("|")):
                s.append(txt(x + 16, y + 72 + i * 19, ln, 12.5, "#555"))
        return "".join(s)

    def lollipop(x, y, label, side="right"):
        """Provided interface: line + circle."""
        dx = 46 if side == "right" else -46
        return (line(x, y, x + dx, y)
                + '<circle cx="%s" cy="%s" r="9" fill="#fff" stroke="%s" stroke-width="1.8"/>'
                % (x + dx, y, LINE)
                + txt(x + dx + (16 if side == "right" else -16), y + 5, label, 12.5, "#444",
                      "start" if side == "right" else "end"))

    def socket(x, y, side="left"):
        """Required interface: half-circle facing the lollipop."""
        r = 15
        if side == "left":
            d = "M %s,%s A %s,%s 0 0 0 %s,%s" % (x, y - r, r, r, x, y + r)
        else:
            d = "M %s,%s A %s,%s 0 0 1 %s,%s" % (x, y - r, r, r, x, y + r)
        return '<path d="%s" fill="none" stroke="%s" stroke-width="1.8"/>' % (d, LINE)

    g.append(comp(120, 200, 400, 150, "Browser SPA",
                  "component", "#eaf1fd",
                  "React 19 + TypeScript + Vite|victim, investigator,|recovery and admin screens"))
    g.append(comp(760, 200, 440, 150, "FSDIRAS API",
                  "component", "#e9f4ec",
                  "FastAPI · 40 endpoints|JWT auth + RBAC · pagination|business rules for all 4 modules"))
    g.append(comp(760, 470, 440, 130, "Detection Service",
                  "component", "#fdf2e6",
                  "FastAPI on :8001 · TF-IDF + LogReg|threshold 0.17, score anchored to 70"))
    g.append(comp(1480, 180, 420, 120, "PDF Reporter",
                  "component", "#f3eefb", "reportlab · case and|recovery reports"))
    g.append(comp(1480, 340, 420, 120, "Notification Gateway",
                  "component", "#f3eefb", "email / SMS · REQ-19|persisted to notifications"))
    g.append(comp(1480, 500, 420, 130, "Evidence Store",
                  "component", "#f3eefb",
                  "AES-256-GCM at rest|size / type / EICAR checks"))
    g.append(comp(760, 740, 440, 130, "Relational Database",
                  "database", "#eef0f3",
                  "PostgreSQL (SQLite fallback)|15 tables · hash-chained custody"))

    def ball(x, y):
        return ('<circle cx="%s" cy="%s" r="9" fill="#fff" stroke="%s" stroke-width="1.8"/>'
                % (x, y, LINE))

    def vsocket(x, y):
        """Required interface facing downwards, cupping a ball below it."""
        r = 15
        return ('<path d="M %s,%s A %s,%s 0 0 1 %s,%s" fill="none" stroke="%s" '
                'stroke-width="1.8"/>' % (x - r, y, r, r, x + r, y, LINE))

    # SPA -> API : assembly connector, the ball is the API's provided interface
    g.append(line(520, 250, 664, 250, LINE, 1.4))
    g.append(socket(664, 250, "left"))
    g.append(ball(700, 250))
    g.append(line(709, 250, 760, 250, LINE, 1.4))
    g.append(txt(636, 222, "REST /api", 12.5, "#444", "middle"))
    g.append(txt(636, 292, "HTTPS · JSON", 12.5, "#555", "middle"))

    # API -> detection, same connector drawn vertically
    g.append(line(980, 350, 980, 406, LINE, 1.4))
    g.append(vsocket(980, 408))
    g.append(ball(980, 430))
    g.append(line(980, 439, 980, 470, LINE, 1.4))
    g.append(txt(1000, 404, "/predict", 12.5, "#444"))
    g.append(txt(1000, 438, "pooled httpx client; falls back", 12.5, "#555"))
    g.append(txt(1000, 456, "to rules-v0 when down", 12.5, "#555"))

    # API -> right-hand components
    for cy, label in ((240, "generate()"), (400, "send()"), (565, "put() / get()")):
        g.append(line(1200, 275, 1340, 275, LINE, 1.4))
        g.append(line(1340, 275, 1340, cy, LINE, 1.4))
        g.append(line(1340, cy, 1480, cy, LINE, 1.4))
        g.append('<circle cx="1455" cy="%s" r="9" fill="#fff" stroke="%s" stroke-width="1.8"/>'
                 % (cy, LINE))
        g.append(txt(1348, cy - 12, label, 12.5, "#444"))

    # API -> database
    g.append(line(980, 350, 980, 350, LINE))
    g.append(line(700, 275, 700, 805, LINE, 1.4))
    g.append(line(700, 275, 760, 275, LINE, 1.4))
    g.append(line(700, 805, 760, 805, LINE, 1.4))
    g.append('<circle cx="736" cy="805" r="9" fill="#fff" stroke="%s" stroke-width="1.8"/>' % LINE)
    g.append(txt(610, 560, "SQLAlchemy", 12.5, "#444"))
    g.append(txt(610, 578, "ORM", 12.5, "#444"))

    g.append(rect(120, 980, 1860, 180, "#f7f9fc", 8, "#cfd8e4", 1.4))
    g.append(txt(144, 1012, "Notation and architecture note", 15, INK, "start", "700"))
    g.append('<circle cx="156" cy="1046" r="9" fill="#fff" stroke="%s" stroke-width="1.8"/>' % LINE)
    g.append(txt(176, 1051, "provided interface (lollipop) — what the component offers",
                 13, "#333"))
    g.append(socket(156, 1082, "left"))
    g.append(txt(176, 1087, "required interface (socket) — what it needs from another",
                 13, "#333"))
    g.append(txt(144, 1124,
                 "Pattern: layered client-server with the ML model isolated behind its own HTTP "
                 "boundary, so it can be retrained, versioned or taken down without the API "
                 "losing the ability to score.", 13, "#555"))
    return page(W, H, "".join(g), "Figure 2 — Component Diagram", "component")


# ======================================================================= mermaid
MERMAID = {}

MERMAID["class"] = ("Figure 3 — Class Diagram (domain model)", """
classDiagram
    direction LR
    class User {
        +int id
        +str full_name
        +str email
        +str phone
        -str hashed_password
        +Role role
        +bool is_active
        +verify_password(raw) bool
    }
    class ScamReport {
        +int id
        +str report_ref
        +str reporter_name
        +ScamCategory category
        +str description
        +Decimal amount_involved
        +int risk_score
        +RiskBand risk_band
    }
    class Case {
        +int id
        +str case_ref
        +CaseStatus status
        +datetime updated_at
        +assign(investigator)
        +transition(status)
    }
    class CaseNote {
        +int id
        +str body
        +datetime created_at
    }
    class Evidence {
        +int id
        +str filename
        +str stored_path
        +str content_type
        +int size_bytes
        +bool is_archived
        +archive(reason)
    }
    class CustodyEvent {
        +int id
        +CustodyAction action
        +str prev_hash
        +str entry_hash
        +compute_entry_hash() str
    }
    class RecoveryRequest {
        +int id
        +str bank_name
        +str ifsc_code
        +Decimal amount_reported
        +Decimal amount_recovered
        +RecoveryStatus status
    }
    class Notification {
        +int id
        +str channel
        +str subject
        +bool is_read
    }
    class DetectionLog {
        +int id
        +int risk_score
        +RiskBand risk_band
        +bool matched_blacklist
        +str model_version
        +int latency_ms
    }
    class BlacklistEntry {
        +int id
        +BlacklistType entry_type
        +str value
    }
    class AuditLog {
        +int id
        +str action
        +str target
    }
    class AwarenessContent {
        +int id
        +str title
        +bool is_published
    }
    class Quiz {
        +int id
        +str title
        +bool is_published
    }
    class QuizQuestion {
        +int id
        +str prompt
        -int correct_index
    }
    class QuizAttempt {
        +int id
        +int score
    }

    User "1" --> "0..*" ScamReport : reports
    ScamReport "1" --> "1" Case : opens
    User "0..1" --> "0..*" Case : assigned
    Case "1" *-- "0..*" CaseNote : notes
    User "1" --> "0..*" CaseNote : author
    Case "1" *-- "0..*" Evidence : evidence
    User "1" --> "0..*" Evidence : uploaded
    Evidence "1" *-- "1..*" CustodyEvent : chain
    User "1" --> "0..*" CustodyEvent : actor
    Case "1" --> "0..1" RecoveryRequest : recovery
    User "1" --> "0..*" RecoveryRequest : raised
    User "1" --> "0..*" Notification : receives
    User "0..1" --> "0..*" DetectionLog : requested
    User "0..1" --> "0..*" BlacklistEntry : added
    User "0..1" --> "0..*" AuditLog : actor
    User "0..1" --> "0..*" AwarenessContent : author
    Quiz "1" *-- "1..*" QuizQuestion : questions
    Quiz "1" --> "0..*" QuizAttempt : attempts
    User "0..1" --> "0..*" QuizAttempt : taken
""")

MERMAID["sequence"] = ("Figure 4 — Sequence Diagram: submit a scam report (REQ-2 → REQ-8)", """
sequenceDiagram
    autonumber
    actor V as Victim
    participant UI as Browser SPA
    participant API as FSDIRAS API
    participant ML as Detection Service
    participant DB as Database
    participant N as Notification Gateway

    V->>UI: fill 3-step report wizard
    UI->>API: POST /api/reports
    API->>API: validate payload (Appendix B)
    API->>DB: SELECT blacklist_entries
    alt value is blacklisted
        DB-->>API: match found
        API->>API: score = 100, band = HIGH
    else not blacklisted
        API->>ML: POST /predict {text}
        ML-->>API: {probability, reasons}
        Note over API,ML: on timeout fall back to rules-v0
        API->>API: anchor probability to 0..100
    end
    API->>DB: INSERT scam_reports + detection_logs
    API->>DB: INSERT cases (case_ref, status = new)
    API->>API: allocate least-loaded investigator
    API->>DB: UPDATE cases.assigned_investigator_id
    API->>N: queue "report received" message
    N->>DB: INSERT notifications
    API-->>UI: 201 {report_ref, case_ref, risk_band}
    UI-->>V: show Case ID and tracking link
""")

MERMAID["state"] = ("Figure 5 — State Machine Diagrams: case and recovery lifecycles", """
stateDiagram-v2
    direction LR
    state "Case lifecycle (REQ-12)" as C {
        [*] --> new : report submitted
        new --> under_investigation : investigator accepts
        under_investigation --> escalated : needs higher authority
        under_investigation --> resolved : outcome recorded
        escalated --> resolved : outcome recorded
        resolved --> closed : victim informed
        closed --> [*]
    }
    state "Recovery lifecycle (REQ-16)" as R {
        [*] --> requested : request raised
        requested --> in_progress : bank contacted
        requested --> rejected : not eligible
        in_progress --> partially_recovered : part of funds returned
        in_progress --> fully_recovered : all funds returned
        in_progress --> rejected : bank declines
        partially_recovered --> fully_recovered : remainder returned
        fully_recovered --> [*]
        partially_recovered --> [*]
        rejected --> [*]
    }
""")

MERMAID["activity"] = ("Figure 6 — Activity Diagram: evidence upload and chain of custody", """
flowchart TD
    S(( )) --> A[Investigator selects file]
    A --> B[/Upload to POST /api/evidence/]
    B --> C{Size and MIME<br/>type allowed?}
    C -- no --> X1[Reject 400] --> E(((  )))
    C -- yes --> D{EICAR / malware<br/>signature?}
    D -- yes --> X2[Reject 400 and audit] --> E
    D -- no --> F[Encrypt with AES-256-GCM]
    F --> G[Store under evidence root]
    G --> H[Read previous entry_hash<br/>for this evidence]
    H --> I[canonical_ts normalises<br/>the timestamp]
    I --> J[compute_entry_hash<br/>prev_hash + fields]
    J --> K[(INSERT custody_events<br/>born hashed)]
    K --> L[Return evidence id]
    L --> E
    style S fill:#1a1a1a,stroke:#1a1a1a
    style E fill:#fff,stroke:#1a1a1a,stroke-width:4px
""")


def mermaid_html(code, fig):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<script src="mermaid.min.js"></script>'
            '<style>html,body{margin:0;padding:0;background:#fff;'
            'font-family:"Segoe UI",Arial,sans-serif}'
            '#wrap{padding:30px 36px 34px;display:inline-block;background:#fff}'
            'h1{font-size:25px;margin:0 0 4px;color:#1a1a1a}'
            '.t{font-size:14px;color:#444;margin:0}'
            '.s{font-size:12.5px;color:#6b7384;margin:2px 0 22px}'
            '.mermaid{background:#fff}</style></head><body><div id="wrap">'
            '<h1>%s</h1><p class="t">%s</p><p class="s">%s</p>'
            '<pre class="mermaid">%s</pre></div>'
            '<script>mermaid.initialize({startOnLoad:true,theme:"base",'
            'themeVariables:{primaryColor:"#eaf1fd",primaryBorderColor:"#1f5fbf",'
            'primaryTextColor:"#1a1a1a",lineColor:"#394150",fontSize:"15px",'
            'fontFamily:"Segoe UI, Arial, sans-serif"},'
            'flowchart:{useMaxWidth:false},sequence:{useMaxWidth:false},'
            'class:{useMaxWidth:false}});</script></body></html>'
            % (esc(fig), esc(TITLE), esc(SUB), esc(code)))


if __name__ == "__main__":
    for name, fn in (("01_usecase", use_case), ("02_component", component)):
        open(os.path.join(HERE, name + ".html"), "w", encoding="utf-8").write(html(fn()))
        print("svg", name)
    order = {"class": "03_class", "sequence": "04_sequence",
             "state": "05_state", "activity": "06_activity"}
    for key, fname in order.items():
        fig, code = MERMAID[key]
        open(os.path.join(HERE, fname + ".html"), "w", encoding="utf-8").write(
            mermaid_html(code.strip(), fig))
        print("mermaid", fname)

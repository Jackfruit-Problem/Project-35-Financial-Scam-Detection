# -*- coding: utf-8 -*-
"""Render every markdown deliverable in this folder to its PDF.

    python make_pdfs.py            # all of them
    python make_pdfs.py architecture.md test-plan.md

Needs `markdown` and `playwright` (`python -m playwright install chromium`).

Two details that matter and are easy to lose:

* `<base href>` points at this folder, so a relative image path in the markdown
  (`uml/02_component.png`) resolves in the PDF as well as it does on GitHub.
* A ```mermaid fence is rendered by mermaid itself rather than printed as a
  block of code, so the Design Diagrams PDF stands on its own away from GitHub.
  The bundle is fetched once into the system temp folder; it is 2.5 MB and does
  not belong in the repository.
"""
import html
import os
import re
import sys
import tempfile
import urllib.request

import markdown
from playwright.sync_api import sync_playwright

DOCS = os.path.dirname(os.path.abspath(__file__))

MERMAID_VERSION = "11.4.1"
MERMAID_URL = f"https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.min.js"
MERMAID_CACHE = os.path.join(tempfile.gettempdir(), f"mermaid-{MERMAID_VERSION}.min.js")

# src -> output name. The order is the order a reviewer would read them in.
JOBS = [
    ("deliverables.md", "FSDIRAS - Deliverables Index.pdf"),
    ("architecture.md", "FSDIRAS - Software Architecture.pdf"),
    ("design-diagrams.md", "FSDIRAS - Design Diagrams.pdf"),
    ("traceability-matrix.md", "FSDIRAS - Traceability Matrix.pdf"),
    ("project-plan.md", "FSDIRAS - Project Plan.pdf"),
    ("test-plan.md", "FSDIRAS - Test Plan.pdf"),
    ("test-report.md", "FSDIRAS - Test Report.pdf"),
    ("quality-report.md", "FSDIRAS - Quality Report.pdf"),
    ("user-manual.md", "FSDIRAS - User Manual.pdf"),
    ("../RUNNING.md", "FSDIRAS - Installation Guide.pdf"),
    ("deployment.md", "FSDIRAS - Deployment Guide.pdf"),
    ("retrospective-sprint-1.md", "FSDIRAS - Sprint 1 Retrospective.pdf"),
    ("retrospective-sprint-2.md", "FSDIRAS - Sprint 2 Retrospective.pdf"),
    ("sprint-retrospective.md", "FSDIRAS - Retrospective Template.pdf"),
    ("viva-prep.md", "FSDIRAS - Viva Prep.pdf"),
]

CSS = """
@page{size:A4;margin:15mm 13mm}
body{font-family:'Segoe UI',Arial,sans-serif;font-size:10.5px;line-height:1.5;color:#1a1a1a}
h1{font-size:21px;margin:0 0 6px;color:#17365d;page-break-after:avoid}
h1+p{margin-top:0}
h2{font-size:14px;margin:18px 0 6px;padding-bottom:4px;border-bottom:2px solid #17365d;
   color:#17365d;page-break-after:avoid}
h3{font-size:11.5px;margin:13px 0 4px;color:#243b53;page-break-after:avoid}
h4{font-size:10.5px;margin:11px 0 3px;color:#243b53;page-break-after:avoid}
table{border-collapse:collapse;width:100%;margin:7px 0 11px;font-size:9px;
      page-break-inside:avoid}
th{background:#eef1f5;text-align:left;padding:4px 5px;border:1px solid #c8cfd8}
td{padding:4px 5px;border:1px solid #dde3ea;vertical-align:top}
code{font-family:Consolas,monospace;font-size:8.6px;background:#f4f6f8;padding:1px 3px;
     border-radius:3px}
pre{background:#1e1e1e;color:#dcdcdc;padding:9px 11px;border-radius:5px;font-size:8.8px;
    line-height:1.35;page-break-inside:avoid;overflow:hidden}
pre code{background:none;color:inherit;font-size:8.8px}
pre.mermaid{background:#fff;color:#000;padding:4px;border:1px solid #e3e8ee;text-align:center}
pre.mermaid svg{max-width:100%;height:auto}
blockquote{border-left:3px solid #9fb6d4;background:#f4f8fd;margin:9px 0;padding:7px 11px;
           color:#2d4259}
hr{border:none;border-top:2px solid #c8cfd8;margin:18px 0}
ul,ol{margin:6px 0 10px;padding-left:20px}
li{margin:2px 0}
strong{color:#111}
img{max-width:100%;height:auto;page-break-inside:avoid}
"""

FENCE = re.compile(r'<pre><code class="language-mermaid">(.*?)</code></pre>', re.DOTALL)


def to_mermaid_blocks(body):
    """Turn fenced mermaid code blocks back into source mermaid can render."""
    count = 0

    def swap(match):
        nonlocal count
        count += 1
        return '<pre class="mermaid">%s</pre>' % html.unescape(match.group(1))

    return FENCE.sub(swap, body), count


def mermaid_bundle():
    if not os.path.exists(MERMAID_CACHE):
        print("fetching mermaid %s ..." % MERMAID_VERSION)
        urllib.request.urlretrieve(MERMAID_URL, MERMAID_CACHE)
    return MERMAID_CACHE.replace("\\", "/")


def main(argv):
    jobs = JOBS
    if argv:
        wanted = set(argv)
        jobs = [j for j in JOBS if j[0] in wanted or os.path.basename(j[0]) in wanted]
        if not jobs:
            sys.exit("nothing matched: %s" % ", ".join(sorted(wanted)))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for src, out in jobs:
            with open(os.path.join(DOCS, src), encoding="utf-8") as handle:
                md = handle.read()

            body = markdown.markdown(
                md, extensions=["tables", "fenced_code", "sane_lists", "attr_list"]
            )
            body, diagrams = to_mermaid_blocks(body)

            doc = (
                "<!doctype html><html><head><meta charset='utf-8'>"
                "<base href='file:///%s/'><style>%s</style></head><body>%s"
                % (DOCS.replace("\\", "/"), CSS, body)
            )
            if diagrams:
                doc += (
                    "<script src='file:///%s'></script>"
                    "<script>mermaid.initialize({startOnLoad:true,theme:'neutral',"
                    "flowchart:{useMaxWidth:true},sequence:{useMaxWidth:true}});</script>"
                    % mermaid_bundle()
                )
            doc += "</body></html>"

            tmp = os.path.join(tempfile.gettempdir(), os.path.basename(src) + ".html")
            with open(tmp, "w", encoding="utf-8") as handle:
                handle.write(doc)

            page = browser.new_page()
            page.goto("file:///" + tmp.replace("\\", "/"))
            if diagrams:
                # Wait for every fence to become an SVG rather than for a fixed
                # delay: a half-drawn diagram in a PDF is worse than a slow build.
                try:
                    page.wait_for_function(
                        "n => document.querySelectorAll('pre.mermaid svg').length === n",
                        arg=diagrams,
                        timeout=60000,
                    )
                except Exception:
                    done = page.eval_on_selector_all("pre.mermaid svg", "els => els.length")
                    print("  WARNING %s: %d of %d diagrams rendered" % (out, done, diagrams))
            page.wait_for_timeout(350)

            dest = os.path.join(DOCS, out)
            page.pdf(path=dest, format="A4", print_background=True)
            print(
                "pdf  %-44s %5d KB  %s"
                % (out, os.path.getsize(dest) // 1024, "%d diagrams" % diagrams if diagrams else "")
            )
            page.close()
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1:])

# -*- coding: utf-8 -*-
"""Render the UML HTML files to PNG and bundle one PDF."""
import os
import sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = r"C:\Users\Mohammed Muaz Iqubal\Desktop\04 Course Project - FSDIRAS (SE)\jackfruit\docs\uml"
NAMES = ["01_usecase", "02_component", "03_class", "04_sequence", "05_state", "06_activity"]

os.makedirs(DEST, exist_ok=True)
sizes = {}

with sync_playwright() as p:
    b = p.chromium.launch()
    for n in NAMES:
        pg = b.new_page(viewport={"width": 1600, "height": 1200}, device_scale_factor=2)
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto("file:///" + os.path.join(HERE, n + ".html").replace("\\", "/"))
        try:
            pg.wait_for_selector("svg", timeout=20000)
        except Exception as e:
            print("NO SVG", n, e, errs[:3])
        pg.wait_for_timeout(1200)
        el = pg.query_selector("#wrap") or pg.query_selector("svg")
        box = el.bounding_box()
        out = os.path.join(DEST, n + ".png")
        el.screenshot(path=out)
        sizes[n] = (round(box["width"]), round(box["height"]))
        print("png", n, sizes[n], os.path.getsize(out) // 1024, "KB", ("ERR " + errs[0]) if errs else "")
        pg.close()

    # one PDF, each diagram on its own landscape page scaled to fit
    pages = []
    for n in NAMES:
        w, h = sizes[n]
        pages.append(
            '<div class="pg"><img src="%s"></div>'
            % ("file:///" + os.path.join(DEST, n + ".png").replace("\\", "/")))
    doc = ('<!doctype html><html><head><meta charset="utf-8"><style>'
           '@page{size:1400px 990px;margin:0}'
           'html,body{margin:0;padding:0;background:#fff}'
           '.pg{width:1400px;height:990px;display:flex;align-items:center;'
           'justify-content:center;page-break-after:always;overflow:hidden}'
           '.pg img{max-width:1340px;max-height:940px;object-fit:contain}'
           '</style></head><body>%s</body></html>' % "".join(pages))
    tmp = os.path.join(HERE, "all.html")
    open(tmp, "w", encoding="utf-8").write(doc)
    pg = b.new_page()
    pg.goto("file:///" + tmp.replace("\\", "/"))
    pg.wait_for_timeout(1500)
    pdf = os.path.join(DEST, "FSDIRAS - UML Diagrams.pdf")
    pg.pdf(path=pdf, width="1400px", height="990px", print_background=True)
    print("pdf", pdf, os.path.getsize(pdf) // 1024, "KB")
    b.close()
